"use client";
import { useRouter } from "next/navigation";
import axios from "@/lib/axios";
import { Button } from "@heroui/button";
import { Card, CardBody, CardHeader } from "@heroui/card";
import { useState, useRef, useEffect } from "react";
import { File, Upload, Loader2, History, CheckCircle2, XCircle, Clock } from "lucide-react";
import { fetchImportHistory, FileImportHistory } from "@/lib/api";
import { Tabs, Tab } from "@heroui/tabs";

export default function ImportCSVPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [importHistory, setImportHistory] = useState<FileImportHistory[]>([]);
  const [historyLoading, setHistoryLoading] = useState(true);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const loadHistory = async () => {
      try {
        const history = await fetchImportHistory();
        setImportHistory(history);
      } catch (err) {
        console.error("Error loading import history:", err);
      } finally {
        setHistoryLoading(false);
      }
    };
    loadHistory();
  }, []);

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

      // Reload history after successful upload
      const history = await fetchImportHistory();
      setImportHistory(history);

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

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString("ru-RU", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const formatFileSize = (bytes?: number) => {
    if (!bytes) return "N/A";
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(2)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  return (
    <main className="p-4 md:p-6 lg:p-8">
          <div className="mb-6">
            <h1 className="text-3xl font-bold mb-2">Импорт файлов</h1>
            <p className="text-primary-foreground">
              Загрузите CSV или XLSX файлы и просмотрите историю загрузок
            </p>
          </div>

          <Tabs aria-label="Import tabs" className="mb-6">
            <Tab key="upload" title="Загрузка">
              <Card className="border border-divider w-full max-w-2xl">
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
            </Tab>
            <Tab key="history" title="История загрузок">
              <Card className="border border-divider">
                <CardHeader className="pb-3">
                  <div className="flex items-center gap-2">
                    <History className="h-5 w-5" />
                    <h3 className="text-lg font-semibold">История загрузок</h3>
                  </div>
                </CardHeader>
                <CardBody>
                  {historyLoading ? (
                    <div className="flex items-center justify-center h-[300px]">
                      <Loader2 className="h-6 w-6 animate-spin text-default-400" />
                    </div>
                  ) : importHistory.length === 0 ? (
                    <div className="flex flex-col items-center justify-center h-[300px] text-default-400">
                      <History className="h-12 w-12 mb-4 opacity-50" />
                      <p>История загрузок пуста</p>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      {importHistory.map((item) => (
                        <div
                          key={item.import_id}
                          className="border border-divider rounded-lg p-4 hover:bg-default-50 transition-colors"
                        >
                          <div className="flex items-start justify-between gap-4">
                            <div className="flex-1">
                              <div className="flex items-center gap-3 mb-2">
                                <File className="h-5 w-5 text-default-400" />
                                <h4 className="font-semibold text-lg">{item.filename}</h4>
                                <span className="px-2 py-1 text-xs rounded-full bg-primary/10 text-primary">
                                  {item.file_type}
                                </span>
                              </div>
                              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
                                <div>
                                  <p className="text-xs text-default-500 mb-1">Создано записей</p>
                                  <p className="font-semibold text-green-600 flex items-center gap-1">
                                    <CheckCircle2 className="h-4 w-4" />
                                    {item.created}
                                  </p>
                                </div>
                                {item.defects_created > 0 && (
                                  <div>
                                    <p className="text-xs text-default-500 mb-1">Дефектов</p>
                                    <p className="font-semibold text-orange-600">
                                      {item.defects_created}
                                    </p>
                                  </div>
                                )}
                                {item.error_count > 0 && (
                                  <div>
                                    <p className="text-xs text-default-500 mb-1">Ошибок</p>
                                    <p className="font-semibold text-red-600 flex items-center gap-1">
                                      <XCircle className="h-4 w-4" />
                                      {item.error_count}
                                    </p>
                                  </div>
                                )}
                                <div>
                                  <p className="text-xs text-default-500 mb-1">Размер файла</p>
                                  <p className="font-semibold">{formatFileSize(item.file_size)}</p>
                                </div>
                              </div>
                            </div>
                            <div className="flex flex-col items-end gap-2">
                              <div className="flex items-center gap-2 text-sm text-default-500">
                                <Clock className="h-4 w-4" />
                                <span>{formatDate(item.imported_at)}</span>
                              </div>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </CardBody>
              </Card>
            </Tab>
          </Tabs>
    </main>
  );
}
