    defects_created = 0

    df['method'] = df['method'].apply(normalize_diagnostic_method)
    df['quality_grade'] = df['quality_grade'].apply(normalize_quality_grade)
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df['ml_label'] = df['ml_label'].apply(normalize_ml_label)
    df['defect_found'] = df['defect_found'].fillna(False).apply(to_bool)
    
    created_objects = []
    for i in df[['object_id', 'date', 'quality_grade', 'ml_label', 'humidity', 'illumination', 'method', 'temperature']].to_dict(orient='records'):
        created_objects.append(Inspection(**i))
        if i['defect_found']:
            created_objects.append(Defect(inspection_id=i['object_id'], defect_type=i['defect_type'], depth=i['depth'], length=i['length'], width=i['width']))
            defects_created += 1

    try:
        db.add_all(created_objects)
        db.commit()
    except Exception as commit_exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(commit_exc))