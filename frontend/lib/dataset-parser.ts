import readXlsxFile from "read-excel-file/browser";

export type CellValue = string | number | boolean | null;

export type DatasetColumn = {
  key: string;
  label: string;
  type: "string" | "number" | "boolean" | "date" | "unknown";
};

export type DatasetRow = {
  rowId: number;
  values: Record<string, CellValue>;
};

export type UploadedDataset = {
  fileName: string;
  format: "csv" | "xlsx";
  columns: DatasetColumn[];
  rows: DatasetRow[];
  warnings: string[];
};

function parseCsv(text: string): unknown[][] {
  const rows: unknown[][] = [];
  let row: string[] = [];
  let value = "";
  let quoted = false;
  for (let index = 0; index < text.length; index += 1) {
    const character = text[index];
    const next = text[index + 1];
    if (character === '"') {
      if (quoted && next === '"') {
        value += '"';
        index += 1;
      } else {
        quoted = !quoted;
      }
    } else if (character === "," && !quoted) {
      row.push(value.trim());
      value = "";
    } else if ((character === "\n" || character === "\r") && !quoted) {
      if (character === "\r" && next === "\n") index += 1;
      row.push(value.trim());
      if (row.some((cell) => cell !== "")) rows.push(row);
      row = [];
      value = "";
    } else {
      value += character;
    }
  }
  row.push(value.trim());
  if (row.some((cell) => cell !== "")) rows.push(row);
  return rows;
}

const REQUIRED_COLUMNS = ["amount", "status"];

function normalizeKey(label: string, index: number) {
  const key = label
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_|_$/g, "");

  return key || `column_${index + 1}`;
}

function normalizeCell(value: unknown): CellValue {
  if (value === undefined || value === null || value === "") return null;
  if (value instanceof Date) return value.toISOString();
  if (typeof value === "string") {
    const trimmed = value.trim();
    if (/^-?\d+(\.\d+)?$/.test(trimmed)) return Number(trimmed);
    return trimmed;
  }
  if (typeof value === "number" || typeof value === "boolean") {
    return value;
  }
  return String(value);
}

function inferColumnType(values: CellValue[]): DatasetColumn["type"] {
  const populated = values.filter((value) => value !== null);
  if (populated.length === 0) return "unknown";
  if (populated.every((value) => typeof value === "number")) return "number";
  if (populated.every((value) => typeof value === "boolean")) return "boolean";
  if (populated.every((value) => typeof value === "string" && !Number.isNaN(Date.parse(value)))) {
    return "date";
  }
  return "string";
}

export async function parseDataset(file: File): Promise<UploadedDataset> {
  const extension = file.name.toLowerCase().split(".").pop();
  if (extension !== "csv" && extension !== "xlsx") {
    throw new Error("Unsupported file type. Upload a CSV or XLSX file.");
  }
  if (file.size > 10 * 1024 * 1024) {
    throw new Error("This file is larger than the 10 MB upload limit.");
  }

  const matrix: unknown[][] = extension === "csv"
    ? parseCsv(await file.text())
    : ((await readXlsxFile(file))[0]?.data as unknown[][] | undefined) ?? [];
  const headerRow = matrix[0] ?? [];
  const labels = headerRow.map((value, index) => String(value ?? `Column ${index + 1}`));
  if (labels.length === 0 || labels.every((label) => !label.trim())) {
    throw new Error("The uploaded file does not contain column headers.");
  }

  const keyCounts = new Map<string, number>();
  const keys = labels.map((label, index) => {
    const baseKey = normalizeKey(label, index);
    const occurrence = keyCounts.get(baseKey) ?? 0;
    keyCounts.set(baseKey, occurrence + 1);
    return occurrence === 0 ? baseKey : `${baseKey}_${occurrence + 1}`;
  });
  const columns: DatasetColumn[] = keys.map((key, index) => ({
    key,
    label: labels[index],
    type: inferColumnType(matrix.slice(1).map((row) => normalizeCell(row[index]))),
  }));
  const rows: DatasetRow[] = matrix.slice(1).map((row, rowIndex) => ({
    rowId: rowIndex + 1,
    values: Object.fromEntries(
      columns.map((column, columnIndex) => [column.key, normalizeCell(row[columnIndex])]),
    ),
  }));

  const warnings: string[] = [];
  const columnKeys = new Set(columns.map((column) => column.key));
  for (const required of REQUIRED_COLUMNS) {
    if (!columnKeys.has(required)) warnings.push(`Missing recommended column: ${required}.`);
  }
  const amountColumn = columns.find((column) => column.key === "amount");
  if (amountColumn) {
    const invalidAmounts = rows.filter((row) => {
      const value = row.values.amount;
      return value !== null && (typeof value !== "number" || !Number.isFinite(value));
    }).length;
    if (invalidAmounts > 0) warnings.push(`${invalidAmounts} rows have non-numeric amounts.`);
  }
  const missingReasons = rows.filter((row) => !row.values.failure_reason).length;
  if (missingReasons > 0 && columnKeys.has("failure_reason")) {
    warnings.push(`${missingReasons} rows have missing failure reasons.`);
  }
  if (rows.length === 0) warnings.push("The file contains headers but no data rows.");

  return {
    fileName: file.name,
    format: extension === "csv" ? "csv" : "xlsx",
    columns,
    rows,
    warnings,
  };
}
