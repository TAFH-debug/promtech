import logging
from typing import Optional, Tuple
import pandas as pd
import numpy as np
from sqlmodel import Session, select
from lightgbm import LGBMClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, accuracy_score

from app.models.inspection import Inspection
from app.models.defect import Defect
from app.models.diagnostic import MLLabel
from app.models.ml_metrics import MLMetrics

logger = logging.getLogger(__name__)


class MLService:
    """Machine Learning service for diagnostic data classification"""
    
    def __init__(self):
        self.model: Optional[LGBMClassifier] = None
        self.method_encoder: Optional[LabelEncoder] = None
        self.quality_grade_encoder: Optional[LabelEncoder] = None
        self.label_encoder: Optional[LabelEncoder] = None
        self.is_trained = False
    
    def prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare features from diagnostic data"""
        features = df.copy()
        
        # Encode method
        if self.method_encoder is None:
            self.method_encoder = LabelEncoder()
            features['method_encoded'] = self.method_encoder.fit_transform(features['method'].astype(str))
        else:
            # Handle unseen methods
            known_methods = set(self.method_encoder.classes_)
            features['method_encoded'] = features['method'].apply(
                lambda x: self.method_encoder.transform([x])[0] if x in known_methods else -1
            )
        
        # Encode quality_grade
        if self.quality_grade_encoder is None:
            self.quality_grade_encoder = LabelEncoder()
            quality_grades = features['quality_grade'].dropna().astype(str)
            if len(quality_grades) > 0:
                self.quality_grade_encoder.fit(quality_grades)
                features['quality_grade_encoded'] = features['quality_grade'].apply(
                    lambda x: self.quality_grade_encoder.transform([str(x)])[0] if pd.notna(x) else -1
                )
            else:
                features['quality_grade_encoded'] = -1
        else:
            known_grades = set(self.quality_grade_encoder.classes_)
            features['quality_grade_encoded'] = features['quality_grade'].apply(
                lambda x: self.quality_grade_encoder.transform([str(x)])[0] 
                if pd.notna(x) and str(x) in known_grades else -1
            )
        features['defect_found_int'] = features['defect_found'].astype(int)
        feature_cols = [
            'method_encoded',
            'temperature',
            'humidity',
            'illumination',
            'param1',
            'param2',
            'param3',
            'defect_found_int',
            'quality_grade_encoded',
        ]
        return features[feature_cols]
    
    def train(self, labeled_data: pd.DataFrame, db: Session = None) -> Tuple[dict, dict]:
        """
        Train or continue training LightGBM model on labeled inspection data
        
        Args:
            labeled_data: DataFrame with labeled inspection data (must have ml_label column)
            db: Optional database session for incremental learning from existing data
        
        Returns:
            Tuple of (training_metrics, test_metrics)
        """
        # Filter only labeled data
        labeled_df = labeled_data[labeled_data['ml_label'].notna()].copy()
        
        if len(labeled_df) < 10:
            logger.warning(f"Not enough labeled data for training: {len(labeled_df)} samples. Need at least 10.")
            return {}, {}
        
        # If model exists and we have existing data, load it for incremental learning
        if self.is_trained and self.model is not None and db is not None:
            # Load existing labeled data from DB for incremental learning
            existing_inspections = db.exec(
                select(Inspection).where(Inspection.ml_label.isnot(None))
            ).all()
            
            if existing_inspections:
                # Get all defect IDs at once
                existing_inspection_ids = [i.inspection_id for i in existing_inspections if i.inspection_id]
                existing_defects_map = {}
                if existing_inspection_ids:
                    all_defects = db.exec(
                        select(Defect).where(Defect.inspection_id.in_(existing_inspection_ids))
                    ).all()
                    # Group defects by inspection_id
                    for defect in all_defects:
                        if defect.inspection_id not in existing_defects_map:
                            existing_defects_map[defect.inspection_id] = []
                        existing_defects_map[defect.inspection_id].append(defect)
                
                # Build DataFrame from existing data
                existing_data = []
                for insp in existing_inspections:
                    defects = existing_defects_map.get(insp.inspection_id, [])
                    defect_found = len(defects) > 0
                    max_depth = max([d.depth for d in defects if d.depth is not None], default=None) if defects else None
                    max_length = max([d.length for d in defects if d.length is not None], default=None) if defects else None
                    max_width = max([d.width for d in defects if d.width is not None], default=None) if defects else None
                    
                    existing_data.append({
                        'method': insp.method.value if insp.method else None,
                        'temperature': insp.temperature,
                        'humidity': insp.humidity,
                        'illumination': insp.illumination,
                        'param1': max_depth,
                        'param2': max_length,
                        'param3': max_width,
                        'defect_found': defect_found,
                        'quality_grade': insp.quality_grade.value if insp.quality_grade else None,
                        'date': insp.date,
                        'ml_label': insp.ml_label.value if insp.ml_label else None,
                    })
                
                existing_df = pd.DataFrame(existing_data)
                # Combine with new data
                labeled_df = pd.concat([existing_df, labeled_df], ignore_index=True)
        
        X = self.prepare_features(labeled_df)
        y = labeled_df['ml_label'].values
        
        # Encode labels
        if self.label_encoder is None:
            self.label_encoder = LabelEncoder()
            y_encoded = self.label_encoder.fit_transform(y)
        else:
            y_encoded = self.label_encoder.transform(y)
        
        # Split data (80% train, 20% test)
        split_idx = int(len(X) * 0.8)
        X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_test = y_encoded[:split_idx], y_encoded[split_idx:]
        
        # Train or continue training model
        if self.model is None or not self.is_trained:
            # Initial training
            num_classes = len(np.unique(y_encoded))
            self.model = LGBMClassifier(
                objective='multiclass',
                num_class=num_classes,
                n_estimators=100,
                learning_rate=0.1,
                max_depth=5,
                random_state=42,
                verbose=-1,
            )
            self.model.fit(
                X_train,
                y_train,
                eval_set=[(X_test, y_test)],
                callbacks=[lambda _: None],  # Suppress output
            )
        else:
            # Incremental learning - continue training on new data
            # LightGBM supports incremental learning by using the existing model as init_model
            try:
                self.model.fit(
                    X_train,
                    y_train,
                    eval_set=[(X_test, y_test)],
                    callbacks=[lambda _: None],
                    init_model=self.model.booster_,
                )
            except Exception as e:
                logger.warning(f"Incremental learning failed, retraining from scratch: {e}")
                # Retrain from scratch if incremental fails
                num_classes = len(np.unique(y_encoded))
                self.model = LGBMClassifier(
                    objective='multiclass',
                    num_class=num_classes,
                    n_estimators=100,
                    learning_rate=0.1,
                    max_depth=5,
                    random_state=42,
                    verbose=-1,
                )
                self.model.fit(
                    X_train,
                    y_train,
                    eval_set=[(X_test, y_test)],
                    callbacks=[lambda _: None],
                )
        
        # Evaluate on test set
        y_pred = self.model.predict(X_test)
        test_accuracy = accuracy_score(y_test, y_pred)
        
        # Get class names
        class_names = self.label_encoder.classes_
        test_report = classification_report(
            y_test, y_pred, 
            target_names=class_names, 
            output_dict=True,
            zero_division=0
        )
        
        # Evaluate on training set
        y_train_pred = self.model.predict(X_train)
        train_accuracy = accuracy_score(y_train, y_train_pred)
        train_report = classification_report(
            y_train, y_train_pred,
            target_names=class_names,
            output_dict=True,
            zero_division=0
        )
        
        self.is_trained = True
        
        training_metrics = {
            'accuracy': train_accuracy,
            'samples': len(X_train),
            'report': train_report,
        }
        
        test_metrics = {
            'accuracy': test_accuracy,
            'samples': len(X_test),
            'report': test_report,
        }
        
        logger.info(f"Model trained: Train accuracy={train_accuracy:.4f}, Test accuracy={test_accuracy:.4f}")
        
        return training_metrics, test_metrics
    
    def save_metrics(
        self, 
        db: Session,
        training_metrics: dict,
        test_metrics: dict,
        prediction_results: dict = None
    ) -> MLMetrics:
        """Save ML metrics to database"""
        metrics = MLMetrics(
            training_accuracy=training_metrics.get('accuracy', 0.0),
            test_accuracy=test_metrics.get('accuracy', 0.0),
            train_samples=training_metrics.get('samples', 0),
            test_samples=test_metrics.get('samples', 0),
            training_report=training_metrics.get('report', {}),
            test_report=test_metrics.get('report', {}),
            label_distribution=prediction_results.get('label_distribution', {}) if prediction_results else {},
            predicted_count=prediction_results.get('predicted', 0) if prediction_results else 0,
        )
        db.add(metrics)
        db.commit()
        db.refresh(metrics)
        return metrics
    
    def predict_unlabeled(self, unlabeled_data: pd.DataFrame, db: Session) -> dict:
        """
        Predict labels for unlabeled inspection data
        
        Args:
            unlabeled_data: DataFrame with unlabeled inspection data (ml_label should be None)
            db: Database session for updating predictions
        
        Returns:
            Dictionary with prediction statistics
        """
        if not self.is_trained or self.model is None:
            return {'predicted': 0, 'error': 'Model not trained'}
        
        # Filter unlabeled data
        unlabeled_df = unlabeled_data[unlabeled_data['ml_label'].isna()].copy()
        
        if len(unlabeled_df) == 0:
            return {'predicted': 0, 'message': 'No unlabeled data found'}
        
        # Prepare features
        X = self.prepare_features(unlabeled_df)
        
        # Get inspection IDs from the dataframe first
        if 'inspection_id' not in unlabeled_df.columns:
            logger.warning("inspection_id column not found in unlabeled data")
            return {
                'predicted': 0,
                'total_unlabeled': len(unlabeled_df),
                'error': 'inspection_id column missing',
            }
        
        inspection_ids = unlabeled_df['inspection_id'].dropna().astype(int).tolist()
        
        if len(inspection_ids) == 0:
            return {'predicted': 0, 'total_unlabeled': len(unlabeled_df), 'message': 'No valid inspection IDs'}
        
        if len(inspection_ids) != len(X):
            logger.warning(f"Mismatch: {len(inspection_ids)} inspection IDs but {len(X)} feature rows")
            # Align them
            unlabeled_df_aligned = unlabeled_df[unlabeled_df['inspection_id'].notna()].copy()
            inspection_ids = unlabeled_df_aligned['inspection_id'].astype(int).tolist()
            X = self.prepare_features(unlabeled_df_aligned)
        
        # Predict
        predictions_encoded = self.model.predict(X)
        predictions = self.label_encoder.inverse_transform(predictions_encoded)
        
        # Batch update inspections - get all at once
        predicted_count = 0
        label_counts = {}
        
        # Get all inspections at once
        inspections_to_update = db.exec(
            select(Inspection).where(Inspection.inspection_id.in_(inspection_ids))
        ).all()
        
        inspection_map = {insp.inspection_id: insp for insp in inspections_to_update}
        
        # Update predictions
        for inspection_id, prediction in zip(inspection_ids, predictions):
            if inspection_id not in inspection_map:
                continue
            
            insp = inspection_map[inspection_id]
            try:
                ml_label = MLLabel(prediction)
                insp.ml_label = ml_label
                predicted_count += 1
                label_counts[prediction] = label_counts.get(prediction, 0) + 1
            except ValueError:
                logger.warning(f"Invalid prediction: {prediction}")
        
        if predicted_count > 0:
            db.commit()
        
        return {
            'predicted': predicted_count,
            'total_unlabeled': len(unlabeled_df),
            'label_distribution': label_counts,
        }


# Global instance
ml_service = MLService()

