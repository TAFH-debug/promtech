"use client";
import { Button } from "@heroui/button";
import { motion, AnimatePresence } from "framer-motion";
import { ArrowBigRight } from "lucide-react";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { Card, CardBody } from "@heroui/card";

export default function Home() {
  const [isExiting, setIsExiting] = useState(false);
  const router = useRouter();

  const handleNavigate = () => {
    setIsExiting(true);
    router.push("/import_csv");
  };

  return (
    <AnimatePresence mode="wait">
      {!isExiting && (
        <motion.main
          key="home-page"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.3 }}
          className="flex min-h-screen flex-col items-center justify-center p-4"
        >
            <motion.div
              initial={{ opacity: 0, translateY: 20 }}
              animate={{ opacity: 1, translateY: 0 }}
              transition={{ duration: 0.5 }}
              exit={{ opacity: 0, translateY: 20, transition: { duration: 0.5 } }}
            >
              <h1 className="text-4xl font-bold">Добро пожаловать в Integrity OS</h1>
            </motion.div>
            <motion.div
              initial={{ opacity: 0, translateY: 20 }}
              animate={{ opacity: 1, translateY: 0 }}
              transition={{ duration: 0.5, delay: 0.5 }}
              exit={{ opacity: 0, translateY: 20, transition: { duration: 0.5 } }}
              className="flex flex-col items-center justify-center"
            >
              <p className="text-lg text-primary-foreground m-6 text-center">
                Платформа для управления и мониторинга состояния труб в реальном времени.
              </p>
            </motion.div>
            <motion.div
              initial={{ opacity: 0, translateY: 20 }}
              animate={{ opacity: 1, translateY: 0 }}
              transition={{ duration: 0.5, delay: 1 }}
              exit={{ opacity: 0, translateY: 20, transition: { duration: 0.5 } }}
              className="flex flex-col items-center justify-center"
            >
              <Button 
                size="lg" 
                color="primary"
                className="bg-primary-500 text-primary-foreground"
                variant="flat"
                onPress={handleNavigate}
              >
                Перейти к панели управления <ArrowBigRight />
              </Button>
            </motion.div>
        </motion.main>
      )}
    </AnimatePresence>
  );
}
