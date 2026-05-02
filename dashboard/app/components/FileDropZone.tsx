"use client";

import { useCallback, useRef, useState } from "react";

interface FileDropZoneProps {
  onFileSelected: (file: File | null) => void;
  file: File | null;
  accept?: string;
  maxBytes?: number;
}

export function FileDropZone({
  onFileSelected,
  file,
  accept = ".html,.htm,.txt,text/html,text/plain",
  maxBytes = 12 * 1024 * 1024,
}: FileDropZoneProps) {
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const handle = useCallback(
    (f: File) => {
      setError(null);
      if (f.size > maxBytes) {
        setError(`File is ${(f.size / 1024 / 1024).toFixed(1)} MB — max is ${maxBytes / 1024 / 1024} MB.`);
        onFileSelected(null);
        return;
      }
      onFileSelected(f);
    },
    [maxBytes, onFileSelected]
  );

  const onDrop = useCallback(
    (e: React.DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      setDragging(false);
      const f = e.dataTransfer.files?.[0];
      if (f) handle(f);
    },
    [handle]
  );

  return (
    <div>
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        onClick={() => inputRef.current?.click()}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            inputRef.current?.click();
          }
        }}
        className={`dropzone ${dragging ? "dropzone--active" : ""} rounded-md p-8 md:p-10 cursor-pointer text-center select-none`}
      >
        <input
          ref={inputRef}
          type="file"
          accept={accept}
          onChange={(e) => {
            const f = e.target.files?.[0];
            if (f) handle(f);
          }}
          className="sr-only"
        />
        <div className="mx-auto w-12 h-12 rounded-full bg-navy-50 flex items-center justify-center mb-4">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.6"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="w-6 h-6 text-navy-700"
            aria-hidden="true"
          >
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="17 8 12 3 7 8" />
            <line x1="12" y1="3" x2="12" y2="15" />
          </svg>
        </div>
        {file ? (
          <div>
            <div className="text-sm font-medium text-navy-700 num">{file.name}</div>
            <div className="text-xs text-ink-3 mt-1 num">
              {(file.size / 1024).toFixed(1)} KB · click to choose another
            </div>
          </div>
        ) : (
          <div>
            <div className="text-base font-medium text-ink">
              Drop a 10-K here, or <span className="text-navy-700 underline">browse</span>
            </div>
            <div className="text-xs text-ink-3 mt-2">
              Accepts .htm, .html, .txt — max {maxBytes / 1024 / 1024} MB
            </div>
          </div>
        )}
      </div>
      {error && (
        <p className="mt-2 text-xs text-verdict-high-text">{error}</p>
      )}
    </div>
  );
}
