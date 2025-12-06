"use client";
import { motion } from "framer-motion";
import { Input } from "@heroui/input";
import { useRouter } from "next/navigation";
import axios from "@/lib/axios";
import { ChangeEvent } from "react";

export default function Home() {
  const router = useRouter();
  
  const onChange = async (e: ChangeEvent) => {
    await axios.postForm("/csv/import/", {
      file: e.target.files[0],
    });

    router.push("/dashboard");
  }

  return (
    <>
      <main className="flex min-h-screen flex-col items-center justify-center p-4">
        <motion.div
          initial={{ opacity: 0, translateY: 20 }}
          animate={{ opacity: 1, translateY: 0 }}
          transition={{ duration: 0.5 }}
          className="flex flex-col items-center justify-center"
        >
          <h1 className="text-4xl font-bold">Импорт CSV файла</h1>
          <p className="text-lg text-primary-foreground m-6 text-center">
            Загрузите ваш CSV файл для начала работы с данными.
          </p>
          <Input
            isRequired
            name="email"
            placeholder="Choose .csv file"
            onChange={onChange}
            type="file"
            color="primary"
            variant="flat"
            accept="csv"
          />
        </motion.div>
      </main>
    </>
  );
}
