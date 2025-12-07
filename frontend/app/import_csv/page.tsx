"use client";
import { motion } from "framer-motion";
import { useRouter } from "next/navigation";
import axios from "@/lib/axios";
import { Button } from "@heroui/button";
import { Card, CardBody } from "@heroui/card";
import { useState, useRef } from "react";
import { File, Upload, Loader2 } from "lucide-react";

export default function ImportCSVPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setError(null);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setError("Пожалуйста, выберите файл");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append("file", selectedFile);

      await axios.post("/csv/import/", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });

      router.push("/dashboard");
    } catch (err: any) {
      setError(err.response?.data?.detail || "Ошибка при загрузке файла");
      setLoading(false);
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file) {
      setSelectedFile(file);
      setError(null);
    }
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
  };

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0, translateY: 20 }}
        animate={{ opacity: 1, translateY: 0 }}
        transition={{ duration: 0.5 }}
        className="flex flex-col items-center justify-center w-full max-w-2xl"
      >
        <h1 className="text-4xl font-bold mb-2">Импорт CSV файла</h1>
        <p className="text-lg text-primary-foreground/80 mb-8 text-center">
          Загрузите ваш CSV или XLSX файл для начала работы с данными.
        </p>

        <Card className="border border-divider w-full">
          <CardBody className="p-6">
            <div
              onDrop={handleDrop}
              onDragOver={handleDragOver}
              className="border-2 border-dashed border-default-300 rounded-lg p-8 text-center cursor-pointer hover:border-primary transition-colors"
              onClick={() => fileInputRef.current?.click()}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".csv,.xlsx,.xls"
                onChange={handleFileSelect}
                className="hidden"
                disabled={loading}
              />

              <div className="flex flex-col items-center gap-4">
                <div className="p-4 rounded-full bg-default-100">
                  <File className="h-8 w-8 text-default-500" />
                </div>
                {selectedFile ? (
                  <div className="flex flex-col items-center gap-2">
                    <p className="font-semibold text-lg">{selectedFile.name}</p>
                    <p className="text-sm text-default-500">
                      {(selectedFile.size / 1024).toFixed(2)} KB
                    </p>
                  </div>
                ) : (
                  <div className="flex flex-col items-center gap-2">
                    <p className="font-semibold text-lg">
                      Нажмите или перетащите файл сюда
                    </p>
                    <p className="text-sm text-default-500">
                      Поддерживаются форматы: CSV, XLSX, XLS
                    </p>
                  </div>
                )}
              </div>
            </div>

            {error && (
              <div className="mt-4 p-3 rounded-lg bg-danger-50 border border-danger-200">
                <p className="text-sm text-danger">{error}</p>
              </div>
            )}

            <div className="flex gap-4 mt-6">
              <Button
                variant="flat"
                className="flex-1"
                onClick={() => fileInputRef.current?.click()}
                disabled={loading}
              >
                <File className="h-4 w-4 mr-2" />
                Выбрать файл
              </Button>
              <Button
                color="primary"
                className="flex-1"
                onClick={handleUpload}
                disabled={!selectedFile || loading}
                isLoading={loading}
              >
                {loading ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Загрузка...
                  </>
                ) : (
                  <>
                    <Upload className="h-4 w-4 mr-2" />
                    Загрузить
                  </>
                )}
              </Button>
            </div>
          </CardBody>
        </Card>
      </motion.div>
    </main>
  );
}
