import React, { useRef, useState } from 'react';
import { UploadCloud, Sparkles, AlertCircle, Loader2 } from 'lucide-react';
import { api } from '../services/api';
import type { DatasetProfile } from '../types';

interface FileUploadProps {
  onUploadSuccess: (profile: DatasetProfile) => void;
}

export const FileUpload: React.FC<FileUploadProps> = ({ onUploadSuccess }) => {
  const [isDragging, setIsDragging] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFile = async (file: File) => {
    if (!file.name.toLowerCase().endsWith('.csv')) {
      setErrorMessage('Please upload a valid .csv file.');
      return;
    }

    setIsLoading(true);
    setErrorMessage(null);

    try {
      const profile = await api.uploadCSV(file);
      onUploadSuccess(profile);
    } catch (err: any) {
      console.error('Upload failed:', err);
      const detail = err.response?.data?.detail || err.message || 'Failed to upload CSV file.';
      setErrorMessage(detail);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleLoadSample = async () => {
    setIsLoading(true);
    setErrorMessage(null);

    try {
      const sampleCsvContent = `order_id,order_date,product_name,category,quantity,unit_price,discount,sales_amount,region,customer_id
ORD-1001,2024-01-05,Wireless Noise-Canceling Headphones,Electronics,2,149.99,0.10,269.98,North,CUST-201
ORD-1001,2024-01-05,Bluetooth Speaker,Electronics,1,59.99,0.00,59.99,North,CUST-201
ORD-1002,2024-01-08,Organic Cotton T-Shirt,Apparel,3,24.50,0.00,73.50,South,CUST-202
ORD-1003,2024-01-12,Ceramic Coffee Mug Set,Home & Kitchen,2,35.00,0.15,59.50,East,CUST-203
ORD-1004,2024-01-15,Mechanical Gaming Keyboard,Electronics,1,120.00,0.05,114.00,West,CUST-204
ORD-1005,2024-01-18,Running Shoes,Apparel,1,89.99,0.20,71.99,North,CUST-205
ORD-1006,2024-01-22,Stainless Steel Water Bottle,Home & Kitchen,4,19.99,0.00,79.96,East,CUST-206
ORD-1007,2024-01-25,Python Data Science Handbook,Books,2,45.00,0.00,90.00,South,CUST-207
ORD-1008,2024-01-28,Smart Fitness Watch,Electronics,1,199.99,0.10,179.99,West,CUST-208
ORD-1009,2024-01-30,Slim Fit Denim Jeans,Apparel,2,49.99,0.00,99.98,North,CUST-209
ORD-1010,2024-02-02,4K Ultra HD Monitor,Electronics,1,349.99,0.15,297.49,East,CUST-210
ORD-1011,2024-02-05,Cast Iron Skillet,Home & Kitchen,1,49.95,0.00,49.95,South,CUST-211
ORD-1012,2024-02-08,Deep Learning Fundamentals,Books,3,39.99,0.10,107.97,North,CUST-212
ORD-1013,2024-02-12,Wireless Noise-Canceling Headphones,Electronics,1,149.99,0.00,149.99,West,CUST-213
ORD-1014,2024-02-14,Yoga Mat Premium,Sports,2,29.99,0.05,56.98,East,CUST-214
ORD-1015,2024-02-18,Waterproof Winter Jacket,Apparel,1,129.99,0.25,97.49,North,CUST-215
ORD-1016,2024-02-21,Robot Vacuum Cleaner,Home & Kitchen,1,289.99,0.20,231.99,West,CUST-216
ORD-1017,2024-02-25,Ergonomic Office Chair,Home & Kitchen,1,220.00,0.10,198.00,South,CUST-217
ORD-1018,2024-02-28,Mechanical Gaming Keyboard,Electronics,2,120.00,0.00,240.00,North,CUST-218
ORD-1019,2024-03-02,Bluetooth Speaker,Electronics,3,59.99,0.10,161.97,East,CUST-219
ORD-1020,2024-03-05,Organic Cotton T-Shirt,Apparel,4,24.50,0.00,98.00,West,CUST-220
ORD-1021,2024-03-09,Air Fryer Pro 5L,Home & Kitchen,1,119.99,0.15,101.99,North,CUST-221
ORD-1022,2024-03-12,Adjustable Dumbbell Set,Sports,1,179.99,0.10,161.99,South,CUST-222
ORD-1023,2024-03-15,4K Ultra HD Monitor,Electronics,2,349.99,0.10,629.98,West,CUST-223
ORD-1024,2024-03-18,Python Data Science Handbook,Books,1,45.00,0.00,45.00,East,CUST-224
ORD-1025,2024-03-22,Smart Fitness Watch,Electronics,2,199.99,0.05,379.98,North,CUST-225
ORD-1026,2024-03-25,Cast Iron Skillet,Home & Kitchen,2,49.95,0.05,94.91,East,CUST-226
ORD-1027,2024-03-28,Running Shoes,Apparel,2,89.99,0.10,161.98,South,CUST-227
ORD-1028,2024-04-02,Wireless Noise-Canceling Headphones,Electronics,3,149.99,0.15,382.47,North,CUST-228
ORD-1028,2024-04-02,Mechanical Gaming Keyboard,Electronics,1,120.00,0.00,120.00,North,CUST-228
ORD-1029,2024-04-05,Ceramic Coffee Mug Set,Home & Kitchen,1,35.00,0.00,35.00,West,CUST-229
ORD-1030,2024-04-09,Designing Data-Intensive Applications,Books,2,49.99,0.00,99.98,East,CUST-230
ORD-1031,2024-04-12,Waterproof Winter Jacket,Apparel,2,129.99,0.20,207.98,South,CUST-231
ORD-1032,2024-04-15,Robot Vacuum Cleaner,Home & Kitchen,1,289.99,0.10,260.99,North,CUST-232
ORD-1033,2024-04-18,Adjustable Dumbbell Set,Sports,2,179.99,0.15,305.98,East,CUST-233
ORD-1034,2024-04-22,Smart Fitness Watch,Electronics,1,199.99,0.00,199.99,West,CUST-234
ORD-1035,2024-04-26,4K Ultra HD Monitor,Electronics,1,349.99,0.20,279.99,North,CUST-235
ORD-1036,2024-04-28,Yoga Mat Premium,Sports,3,29.99,0.00,89.97,South,CUST-236
ORD-1037,2024-04-30,Slim Fit Denim Jeans,Apparel,1,49.99,0.00,49.99,West,CUST-237`;

      const blob = new Blob([sampleCsvContent], { type: 'text/csv' });
      const sampleFile = new File([blob], 'ecommerce_sales_sample.csv', { type: 'text/csv' });
      const profile = await api.uploadCSV(sampleFile);
      onUploadSuccess(profile);
    } catch (err: any) {
      console.error('Failed to load sample dataset:', err);
      setErrorMessage(err.message || 'Failed to load sample dataset.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="w-full max-w-3xl mx-auto my-10 px-4">
      {/* Title & Introduction */}
      <div className="text-center mb-8">
        <h2 className="text-3xl font-extrabold text-slate-900 tracking-tight sm:text-4xl">
          E-Commerce Sales Intelligence
        </h2>
        <p className="mt-3 text-base text-slate-600 max-w-xl mx-auto leading-relaxed">
          Upload any sales CSV file. The agent infers your schema, computes verified metrics, and generates interactive charts and business insights.
        </p>
      </div>

      {/* Drag & Drop Upload Container */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`relative cursor-pointer rounded-3xl border-2 border-dashed p-10 sm:p-16 text-center transition-all duration-200 shadow-sm ${
          isDragging
            ? 'border-indigo-600 bg-indigo-50/70 scale-[1.01] shadow-md'
            : 'border-slate-300 bg-white hover:border-indigo-500 hover:bg-slate-50/50 hover:shadow-md'
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv"
          className="hidden"
          onChange={(e) => {
            if (e.target.files && e.target.files[0]) {
              handleFile(e.target.files[0]);
            }
          }}
        />

        {isLoading ? (
          <div className="flex flex-col items-center justify-center py-6">
            <Loader2 className="w-12 h-12 text-indigo-600 animate-spin mb-4" />
            <p className="text-base font-semibold text-slate-900">
              Profiling Dataset & Inferring Columns...
            </p>
            <p className="text-xs text-slate-500 mt-1.5">
              Calculating statistical distributions, detecting revenue, and mapping roles
            </p>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center">
            <div className="w-16 h-16 rounded-2xl bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600 mb-5 shadow-sm group-hover:scale-105 transition-transform">
              <UploadCloud className="w-8 h-8" />
            </div>

            <p className="text-base font-semibold text-slate-900 mb-1.5">
              Drag and drop your sales CSV here, or{' '}
              <span className="text-indigo-600 underline decoration-indigo-300 underline-offset-4">
                browse files
              </span>
            </p>
            <p className="text-xs text-slate-500 mt-1">
              Supports any CSV structure • Up to 20MB • Encoding resilient
            </p>
          </div>
        )}
      </div>

      {/* Error Alert */}
      {errorMessage && (
        <div className="mt-5 p-4 rounded-2xl bg-rose-50 border border-rose-200 text-rose-800 flex items-start gap-3 text-xs shadow-sm">
          <AlertCircle className="w-4 h-4 text-rose-600 flex-shrink-0 mt-0.5" />
          <div className="flex-1 font-medium">{errorMessage}</div>
        </div>
      )}

      {/* Sample Dataset Action */}
      <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-3 text-xs text-slate-500">
        <span>Want to test immediately?</span>
        <button
          type="button"
          onClick={handleLoadSample}
          disabled={isLoading}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-white hover:bg-slate-50 text-indigo-600 hover:text-indigo-700 font-semibold border border-indigo-200 hover:border-indigo-300 transition-all shadow-sm"
        >
          <Sparkles className="w-4 h-4 text-indigo-600" />
          <span>Load Synthetic E-Commerce Sample</span>
        </button>
      </div>
    </div>
  );
};
