import { DatasetColumn, DatasetRow, UploadedDataset, CellValue } from "./dataset-parser";

export type QueryResult = {
  question: string;
  answer: string;
  operation: string;
  rowsUsed: number;
  supporting: string[];
  table?: { columns: DatasetColumn[]; rows: DatasetRow[] };
};

function numericValue(value: CellValue) {
  if (typeof value === "number") return Number.isFinite(value) ? value : null;
  if (typeof value === "string" && value.trim() !== "") {
    const parsed = Number(value.replace(/[^0-9.-]/g, ""));
    return Number.isFinite(parsed) ? parsed : null;
  }
  return null;
}

function displayValue(value: number) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(value);
}

function findColumn(dataset: UploadedDataset, names: string[]) {
  return dataset.columns.find((column) => names.includes(column.key));
}

function failedRows(dataset: UploadedDataset) {
  const status = findColumn(dataset, ["status"]);
  if (!status) return dataset.rows;
  return dataset.rows.filter((row) => String(row.values[status.key] ?? "").toLowerCase() === "failed");
}

function successfulRows(dataset: UploadedDataset) {
  const status = findColumn(dataset, ["status", "payment_status"]);
  if (!status) return [];
  return dataset.rows.filter((row) => String(row.values[status.key] ?? "").toLowerCase() === "success");
}

function groupRevenue(rows: DatasetRow[], groupKey: string, amountKey: string) {
  const totals = new Map<string, { amount: number; count: number }>();
  for (const row of rows) {
    const group = String(row.values[groupKey] ?? "Unknown");
    const amount = numericValue(row.values[amountKey]) ?? 0;
    const current = totals.get(group) ?? { amount: 0, count: 0 };
    totals.set(group, { amount: current.amount + amount, count: current.count + 1 });
  }
  return [...totals.entries()]
    .map(([label, value]) => ({ label, ...value }))
    .sort((left, right) => right.amount - left.amount || left.label.localeCompare(right.label));
}

export function answerDatasetQuestion(dataset: UploadedDataset, question: string): QueryResult {
  const normalized = question.trim().toLowerCase();
  if (!normalized) throw new Error("Ask a question about the uploaded data.");
  if (dataset.rows.length === 0) throw new Error("There are no data rows to query.");

  const amount = findColumn(dataset, ["amount", "payment_amount", "value"]);
  const status = findColumn(dataset, ["status", "payment_status"]);
  const reason = findColumn(dataset, ["failure_reason", "reason", "failure"]);
  const customer = findColumn(dataset, ["customer", "customer_name", "customer_id"]);
  if ((normalized.includes("revenue") || normalized.includes("amount")) && !amount) {
    throw new Error("I can't calculate revenue because an amount column is not present.");
  }

  const failed = failedRows(dataset);
  if (normalized.includes("which failure reason") || normalized.includes("top failure reason")) {
    if (!reason || !amount) throw new Error("I need failure_reason and amount columns for that analysis.");
    const top = groupRevenue(failed, reason.key, amount.key)[0];
    if (!top) throw new Error("No failed payment rows were found.");
    return {
      question,
      answer: top.label,
      operation: "Highest failed revenue by failure reason",
      rowsUsed: failed.length,
      supporting: [`Failed revenue: ${displayValue(top.amount)}`, `${top.count} failed payments in this group`],
    };
  }

  if (normalized.includes("top 10") && normalized.includes("customer")) {
    if (!customer || !amount) throw new Error("I need customer and amount columns for that analysis.");
    const top = groupRevenue(failed, customer.key, amount.key).slice(0, 10);
    return {
      question,
      answer: `Top ${top.length} customers by failed revenue`,
      operation: "Rank failed revenue by customer",
      rowsUsed: failed.length,
      supporting: top.map((item, index) => `${index + 1}. ${item.label}: ${displayValue(item.amount)}`),
    };
  }

  const insufficient = normalized.includes("insufficient funds");
  const scopedRows = insufficient && reason
    ? failed.filter((row) => String(row.values[reason.key] ?? "").toLowerCase().includes("insufficient_funds") || String(row.values[reason.key] ?? "").toLowerCase().includes("insufficient funds"))
    : failed;

  if (normalized.includes("how many") || normalized.includes("number of")) {
    if (normalized.includes("failed") && !status) throw new Error("I need a status column to count failed payments.");
    const rowsToCount = normalized.includes("failed") || insufficient ? scopedRows : dataset.rows;
    return {
      question,
      answer: `${rowsToCount.length.toLocaleString("en-IN")} payments`,
      operation: normalized.includes("failed") || insufficient ? "Count failed payments" : "Count uploaded payments",
      rowsUsed: rowsToCount.length,
      supporting: [status && (normalized.includes("failed") || insufficient) ? `${rowsToCount.length} rows matched status = failed` : "All uploaded rows were counted"],
    };
  }

  if (normalized.includes("average") || normalized.includes("avg")) {
    if (!amount) throw new Error("I need an amount column to calculate an average.");
    const values = scopedRows.map((row) => numericValue(row.values[amount!.key])).filter((value): value is number => value !== null);
    if (values.length === 0) throw new Error("No numeric amounts are available for this question.");
    const total = values.reduce((sum, value) => sum + value, 0);
    return { question, answer: displayValue(total / values.length), operation: "Average failed payment amount", rowsUsed: values.length, supporting: [`Calculated from ${values.length} numeric rows`] };
  }

  if (normalized.includes("total") || normalized.includes("revenue at risk") || normalized.includes("failed revenue")) {
    const isFailedRevenue = normalized.includes("failed") || normalized.includes("at risk") || insufficient;
    const rowsToSum = isFailedRevenue
      ? scopedRows
      : normalized.includes("successful")
        ? successfulRows(dataset)
        : dataset.rows;
    const total = rowsToSum.reduce((sum, row) => sum + (numericValue(row.values[amount!.key]) ?? 0), 0);
    return {
      question,
      answer: displayValue(total),
      operation: isFailedRevenue ? (insufficient ? "Sum failed revenue for insufficient funds" : "Sum failed revenue") : normalized.includes("successful") ? "Sum successful revenue" : "Sum total revenue",
      rowsUsed: rowsToSum.length,
      supporting: [`${rowsToSum.length.toLocaleString("en-IN")} rows included`, "Calculated directly from the uploaded amount column"],
    };
  }

  throw new Error("I can answer totals, failed-payment counts, failure-reason revenue, averages, and top customers from this dataset.");
}
