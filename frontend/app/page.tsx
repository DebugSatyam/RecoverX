"use client";

import { useEffect, useState } from "react";
import {
  Area,
  AreaChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

const recoveryData = [
  { day: "Mon", recovered: 28000, risk: 52000 },
  { day: "Tue", recovered: 41000, risk: 61000 },
  { day: "Wed", recovered: 36000, risk: 58000 },
  { day: "Thu", recovered: 63000, risk: 76000 },
  { day: "Fri", recovered: 58000, risk: 69000 },
  { day: "Sat", recovered: 82000, risk: 94000 },
  { day: "Sun", recovered: 96000, risk: 102000 },
];

type RecoveryPayment = {
  recovery_id: number;
  payment_id: number;
  customer: string;
  amount: number;
  reason: string | null;
  probability: number | null;
  action: string | null;
  status: string;
  policy_decision: string | null;
  execution_result: string | null;
};

function formatMoney(value: number) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(value);
}

type RiskOverview = {
  revenue_at_risk: number;
  expected_recoverable_revenue: number;
  high_recovery_cases: number;
  medium_recovery_cases: number;
  low_recovery_cases: number;
};

function AnimatedNumber({
  target,
  prefix = "",
}: {
  target: number;
  prefix?: string;
}) {
  const [value, setValue] = useState(0);

  useEffect(() => {
    let frame: number;
    const start = performance.now();
    const duration = 900;

    const animate = (now: number) => {
      const progress = Math.min((now - start) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);

      setValue(Math.round(target * eased));

      if (progress < 1) {
        frame = requestAnimationFrame(animate);
      }
    };

    frame = requestAnimationFrame(animate);

    return () => cancelAnimationFrame(frame);
  }, [target]);

  return (
    <>
      {prefix}
      {value.toLocaleString("en-IN")}
    </>
  );
}

export default function Home() {
  const [active, setActive] = useState("Overview");

  const [payments, setPayments] =
    useState<RecoveryPayment[]>([]);

  const [queueFilter, setQueueFilter] =
    useState("All");

  const [selectedPayment, setSelectedPayment] =
    useState<RecoveryPayment | null>(null);

  const [overviewLoading, setOverviewLoading] = useState(true);
  const [overview, setOverview] = useState<any>(null);

  const [aiRecommendation, setAiRecommendation] = useState<any>(null);
  const [aiLoading, setAiLoading] = useState(false);

  const [executionLoading, setExecutionLoading] = useState(false);
  const [executionResult, setExecutionResult] = useState<any>(null);

  useEffect(() => {
    async function fetchRecoveryQueue() {
      try {
        const response = await fetch(
          "http://127.0.0.1:8000/recovery/queue"
        );

        if (!response.ok) {
          throw new Error("Failed to fetch recovery queue");
        }

        const data = await response.json();

        setPayments(data.queue);
      } catch (error) {
        console.error(
          "[browser] RecoverX recovery queue error:",
          error
        );
      }
    }

    fetchRecoveryQueue();
  }, []);

  useEffect(() => {
    async function fetchOverview() {
      try {
        setOverviewLoading(true);

        const response = await fetch(
          "http://127.0.0.1:8000/risk/overview"
        );

        if (!response.ok) {
          throw new Error("Failed to fetch overview");
        }

        const data = await response.json();

        setOverview(data);
      } catch (error) {
        console.error(
          "[browser] RecoverX overview error:",
          error
        );
      } finally {
        setOverviewLoading(false);
      }
    }

    fetchOverview();
  }, []);

  async function fetchAIRecommendation(paymentId: number) {
    try {
      setAiLoading(true);
      setAiRecommendation(null);

      const response = await fetch(
        `http://127.0.0.1:8000/ai/groq-recommendation/${paymentId}`
      );

      if (!response.ok) {
        throw new Error("Failed to fetch AI recommendation");
      }

      const data = await response.json();

      setAiRecommendation(data);
    } catch (error) {
      console.error(
        "[browser] RecoverX AI recommendation error:",
        error
      );
    } finally {
      setAiLoading(false);
    }
  }

  const navigation = [
    { name: "Overview", icon: "⌂" },
    { name: "Recovery", icon: "↗" },
    { name: "Customers", icon: "○" },
    { name: "AI Decisions", icon: "✦" },
    { name: "Audit Log", icon: "≡" },
  ];

  async function executeRecovery(recoveryId: number) {
    try {
      setExecutionLoading(true);
      setExecutionResult(null);

      const response = await fetch(
        `http://127.0.0.1:8000/recovery/execute/${recoveryId}`,
        {
          method: "POST",
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Failed to execute recovery");
      }

      setExecutionResult(data);

      // Refresh queue after execution
      const queueResponse = await fetch(
        "http://127.0.0.1:8000/recovery/queue"
      );

      if (queueResponse.ok) {
        const queueData = await queueResponse.json();
        setPayments(queueData.queue);
      }
    } catch (error) {
      console.error(
        "[browser] RecoverX recovery execution error:",
        error
      );
    } finally {
      setExecutionLoading(false);
    }
  }
  return (
    <main className="min-h-screen bg-[#0b0c0d] text-[#f4f4f2]">
      {/* Ambient light */}
      <div className="pointer-events-none fixed inset-0 overflow-hidden">
        <div className="absolute -left-40 -top-40 h-[500px] w-[500px] rounded-full bg-emerald-500/[0.035] blur-[120px]" />
        <div className="absolute right-[-200px] top-[35%] h-[500px] w-[500px] rounded-full bg-blue-500/[0.025] blur-[140px]" />
      </div>

      <div className="relative flex min-h-screen">
        {/* SIDEBAR */}
        <aside className="hidden w-[240px] shrink-0 border-r border-white/[0.07] bg-[#0b0c0d] px-5 py-6 lg:flex lg:flex-col">
          <div className="mb-12 px-1">
            <div className="group flex cursor-pointer items-center gap-3">
              {/* RecoverX brand mark */}
              <div className="relative flex h-9 w-9 shrink-0 items-center justify-center">
                <div className="absolute inset-0 rounded-[11px] border border-white/[0.12] bg-white/[0.045] transition-all duration-300 group-hover:border-emerald-300/30 group-hover:bg-emerald-300/[0.06]" />

                <svg
                  viewBox="0 0 32 32"
                  className="relative h-[22px] w-[22px] transition-transform duration-300 group-hover:scale-110"
                  fill="none"
                >
                  <path
                    d="M8 8L24 24"
                    stroke="currentColor"
                    strokeWidth="2.8"
                    strokeLinecap="round"
                    className="text-white"
                  />

                  <path
                    d="M24 8L14.5 17.5"
                    stroke="currentColor"
                    strokeWidth="2.8"
                    strokeLinecap="round"
                    className="text-emerald-300"
                  />

                  <path
                    d="M11.5 20.5L8 24"
                    stroke="currentColor"
                    strokeWidth="2.8"
                    strokeLinecap="round"
                    className="text-emerald-300"
                  />
                </svg>
              </div>

              {/* Wordmark */}
              <div className="leading-none">
                <div className="flex items-baseline">
                  <span className="text-[16px] font-semibold tracking-[-0.045em] text-white">
                    Recover
                  </span>

                  <span className="text-[16px] font-semibold tracking-[-0.045em] text-emerald-300">
                    X
                  </span>
                </div>

                <div className="mt-[5px] text-[9px] font-medium uppercase tracking-[0.17em] text-white/25">
                  Revenue intelligence
                </div>
              </div>
            </div>
          </div>

          <div className="mb-3 px-2 text-[10px] font-medium uppercase tracking-[0.18em] text-white/25">
            Workspace
          </div>

          <nav className="space-y-1">
            {navigation.map((item) => {
              const isActive = active === item.name;

              return (
                <button
                  key={item.name}
                  onClick={() => setActive(item.name)}
                  className={`group flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left text-[13px] transition-all duration-200 ${
                    isActive
                      ? "bg-white/[0.07] text-white"
                      : "text-white/45 hover:bg-white/[0.035] hover:text-white/80"
                  }`}
                >
                  <span
                    className={`w-5 text-center text-[15px] ${
                      isActive ? "text-white" : "text-white/30"
                    }`}
                  >
                    {item.icon}
                  </span>

                  <span>{item.name}</span>

                  {item.name === "Recovery" && (
                    <span className="ml-auto rounded-full bg-emerald-400/10 px-1.5 py-0.5 text-[9px] text-emerald-300">
                      24
                    </span>
                  )}
                </button>
              );
            })}
          </nav>

          <div className="mt-auto">
            <div className="mb-4 border-t border-white/[0.06]" />

            <div className="rounded-xl border border-white/[0.07] bg-white/[0.025] p-3.5">
              <div className="mb-2 flex items-center gap-2">
                <span className="relative flex h-2 w-2">
                  <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-50" />
                  <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-400" />
                </span>

                <span className="text-[11px] font-medium text-white/70">
                  Recovery engine
                </span>
              </div>

              <p className="text-[10px] leading-4 text-white/30">
                Monitoring failed payments and evaluating recovery actions.
              </p>
            </div>
          </div>
        </aside>

        {/* MAIN */}
        <section className="min-w-0 flex-1">
          {/* TOP BAR */}
          <header className="flex h-[72px] items-center justify-between border-b border-white/[0.07] px-6 lg:px-10">
            <div className="flex items-center gap-3">
              <div className="lg:hidden flex h-8 w-8 items-center justify-center rounded-lg bg-white text-black font-black">
                R
              </div>

              <div>
                <div className="text-[12px] text-white/30">
                  {active}
                </div>
                <div className="text-[13px] font-medium">
                  Revenue recovery
                </div>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <div className="hidden rounded-full border border-white/[0.08] px-3 py-1.5 text-[10px] text-white/40 sm:block">
                Test environment
              </div>

              <button className="flex h-9 w-9 items-center justify-center rounded-full border border-white/[0.08] text-sm text-white/50 transition hover:border-white/20 hover:text-white">
                ♧
              </button>

              <div className="flex h-9 w-9 items-center justify-center rounded-full bg-white/[0.08] text-[11px] font-semibold">
                SM
              </div>
            </div>
          </header>

          <div className="mx-auto max-w-[1450px] px-6 py-8 lg:px-10 lg:py-10">
            {/* INTRO */}
            <div className="mb-10 flex flex-col justify-between gap-5 md:flex-row md:items-end">
              <div>
                <p className="mb-2 text-[11px] font-medium uppercase tracking-[0.16em] text-white/30">
                  Sunday · August 31
                </p>

                <h1 className="text-[30px] font-semibold tracking-[-0.04em] sm:text-[38px]">
                  Revenue, recovered.
                </h1>

                <p className="mt-2 max-w-lg text-[13px] leading-6 text-white/40">
                  RecoverX is watching failed payments, understanding why they
                  failed, and finding the safest way to recover them.
                </p>
              </div>

              <button className="group flex w-fit items-center gap-2 rounded-lg border border-white/[0.1] bg-white/[0.035] px-4 py-2.5 text-[12px] font-medium transition-all hover:border-white/20 hover:bg-white/[0.06]">
                View recovery queue
                <span className="transition-transform duration-200 group-hover:translate-x-1">
                  →
                </span>
              </button>
            </div>

            {/* KPI ROW */}
            <Metric
              label="Revenue at risk"
              value={
                <>
                  ₹
                  {overviewLoading ? (
                    <span className="inline-block h-8 w-28 animate-pulse rounded bg-white/[0.08]" />
                  ) : (
                    <AnimatedNumber target={overview?.revenue_at_risk ?? 0} />
                  )}
                </>
              }
              change="Live"
              positive={false}
              large
            />
            <Metric
              label="Expected recoverable"
              value={
                <>
                  ₹
                  {overviewLoading ? (
                    <span className="inline-block h-7 w-24 animate-pulse rounded bg-white/[0.08]" />
                  ) : (
                    <AnimatedNumber
                      target={overview?.expected_recoverable_revenue ?? 0}
                    />
                  )}
                </>
              }
              change="Live"
              positive
            />
            <Metric
              label="Recovery rate"
              value={
                overview && overview.revenue_at_risk > 0
                  ? `${(
                      (overview.expected_recoverable_revenue /
                        overview.revenue_at_risk) *
                      100
                    ).toFixed(1)}%`
                  : "—"
              }
              change="Calculated"
              positive
            />
            <Metric
              label="Active actions"
              value={
                overview
                  ? overview.high_recovery_cases +
                    overview.medium_recovery_cases +
                    overview.low_recovery_cases
                  : "—"
              }
              change={
                overview
                  ? `${overview.high_recovery_cases} high priority`
                  : "Loading"
              }
              positive
            />
            {/* CHART + AI */}
            <div className="grid gap-6 xl:grid-cols-[1.65fr_0.85fr]">
              {/* CHART */}
              <section className="rounded-xl border border-white/[0.07] bg-white/[0.018] p-5 sm:p-6">
                <div className="mb-8 flex items-start justify-between">
                  <div>
                    <h2 className="text-[14px] font-medium">
                      Recovery performance
                    </h2>
                    <p className="mt-1 text-[11px] text-white/30">
                      Recovered revenue over the last 7 days
                    </p>
                  </div>

                  <button className="rounded-md border border-white/[0.08] px-2.5 py-1.5 text-[10px] text-white/45 hover:text-white">
                    7 days
                  </button>
                </div>

                <div className="h-[290px] w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart
                      data={recoveryData}
                      margin={{ top: 10, right: 5, left: -15, bottom: 0 }}
                    >
                      <defs>
                        <linearGradient
                          id="recoverGradient"
                          x1="0"
                          y1="0"
                          x2="0"
                          y2="1"
                        >
                          <stop
                            offset="0%"
                            stopColor="#8ee6bd"
                            stopOpacity={0.2}
                          />
                          <stop
                            offset="100%"
                            stopColor="#8ee6bd"
                            stopOpacity={0}
                          />
                        </linearGradient>
                      </defs>

                      <XAxis
                        dataKey="day"
                        axisLine={false}
                        tickLine={false}
                        tick={{ fill: "#ffffff45", fontSize: 10 }}
                      />

                      <YAxis
                        axisLine={false}
                        tickLine={false}
                        tick={{ fill: "#ffffff30", fontSize: 10 }}
                        tickFormatter={(value) => `₹${value / 1000}k`}
                      />

                      <Tooltip
                        contentStyle={{
                          background: "#151718",
                          border: "1px solid rgba(255,255,255,.1)",
                          borderRadius: "8px",
                          fontSize: "11px",
                        }}
                        formatter={(value) => [
                          formatMoney(Number(value)),
                          "Recovered",
                        ]}
                      />

                      <Area
                        type="monotone"
                        dataKey="recovered"
                        stroke="#8ee6bd"
                        strokeWidth={2}
                        fill="url(#recoverGradient)"
                        animationDuration={1200}
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </section>

              {/* AI PANEL */}
              <section className="relative overflow-hidden rounded-xl border border-white/[0.07] bg-[#111314] p-6">
                <div className="absolute right-[-80px] top-[-80px] h-40 w-40 rounded-full bg-emerald-300/[0.06] blur-[70px]" />

                <div className="relative">
                  <div className="mb-8 flex items-center justify-between">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-[14px]">✦</span>
                        <h2 className="text-[14px] font-medium">
                          AI recommendation
                        </h2>
                      </div>

                      <p className="mt-1 text-[11px] text-white/30">
                        Latest case evaluated
                      </p>
                    </div>

                    <span className="rounded-full border border-emerald-400/15 bg-emerald-400/[0.06] px-2.5 py-1 text-[9px] text-emerald-300">
                      87% confidence
                    </span>
                  </div>

                  <div className="mb-5">
                    <div className="mb-1 text-[10px] uppercase tracking-[0.14em] text-white/25">
                      Payment #1842
                    </div>

                    <div className="text-[28px] font-semibold tracking-[-0.04em]">
                      ₹4,999
                    </div>

                    <div className="mt-1 text-[11px] text-white/35">
                      Insufficient funds · historically reliable customer
                    </div>
                  </div>

                  <div className="mb-6 rounded-lg border border-white/[0.06] bg-black/20 p-4">
                    <div className="mb-2 text-[10px] uppercase tracking-[0.12em] text-white/25">
                      Diagnosis
                    </div>

                    <p className="text-[12px] leading-5 text-white/65">
                      The customer has a strong successful-payment history.
                      Waiting before another attempt gives the payment a better
                      chance of succeeding.
                    </p>
                  </div>

                  <div className="mb-6 flex items-center justify-between border-b border-white/[0.06] pb-5">
                    <div>
                      <div className="text-[10px] text-white/25">
                        Recommended action
                      </div>
                      <div className="mt-1 text-[13px] font-medium">
                        Retry after 6 hours
                      </div>
                    </div>

                    <span className="text-[18px] text-emerald-300">→</span>
                  </div>

                  <div className="flex items-center justify-between">
                    <div>
                      <div className="text-[10px] text-white/25">
                        Policy decision
                      </div>
                      <div className="mt-1 flex items-center gap-1.5 text-[11px] text-emerald-300">
                        <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
                        Approved
                      </div>
                    </div>

                    <button className="rounded-lg bg-white px-3.5 py-2 text-[11px] font-semibold text-black transition hover:bg-white/90 active:scale-[0.98]">
                      Review action
                    </button>
                  </div>
                </div>
              </section>
            </div>

            {/* RECOVERY QUEUE */}
            <section className="mt-6 overflow-hidden rounded-xl border border-white/[0.07] bg-white/[0.018]">
              <div className="flex flex-col justify-between gap-4 border-b border-white/[0.07] p-5 sm:flex-row sm:items-center sm:px-6">
                <div>
                  <h2 className="text-[14px] font-medium">
                    Recovery queue
                  </h2>

                  <p className="mt-1 text-[11px] text-white/30">
                    Payments where RecoverX sees a viable recovery path.
                  </p>
                </div>

                <div className="flex gap-1 rounded-lg border border-white/[0.07] p-1">
                  {["All", "Ready", "Review"].map((filter) => (
                    <button
                      key={filter}
                      className={`rounded-md px-3 py-1.5 text-[10px] ${
                        queueFilter === filter
                          ? "bg-white/[0.08] text-white"
                          : "text-white/35 hover:text-white/70"
                      }`}
                    >
                      {filter}
                    </button>
                  ))}
                </div>
              </div>

              <div className="divide-y divide-white/[0.055]">
                {payments.filter((payment) => {
                  if (queueFilter === "All") return true;
                  return payment.status === queueFilter;
                }).map((payment) => (
                  <button
                    key={payment.recovery_id}
                    onClick={() => {
                      setSelectedPayment(payment);
                      fetchAIRecommendation(payment.payment_id);
                    }}
                    className="group grid w-full grid-cols-[1fr_auto] gap-4 p-5 text-left transition-colors hover:bg-white/[0.025] sm:grid-cols-[1fr_1fr_auto_auto] sm:items-center sm:px-6"
                  >
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-[12px] font-medium">
                          {payment.payment_id}
                        </span>

                        <span className="text-[10px] text-white/25">
                          {payment.customer}
                        </span>
                      </div>

                      <div className="mt-1 text-[10px] text-white/30">
                        {payment.reason}
                      </div>
                    </div>

                    <div className="hidden sm:block">
                      <div className="text-[12px]">
                        {formatMoney(payment.amount)}
                      </div>

                      <div className="mt-1 text-[10px] text-white/25">
                        {payment.action}
                      </div>
                    </div>

                    <div className="hidden text-right sm:block">
                      <div className="text-[12px] font-medium">
                        {payment.probability !== null
                         ? `${Math.round(payment.probability * 100)}%`
                         : "—"}
                      </div>

                      <div className="mt-1 text-[9px] text-white/25">
                        recovery probability
                      </div>
                    </div>

                    <div className="flex items-center gap-3">
                      <span
                        className={`rounded-full border px-2 py-1 text-[9px] ${
                          payment.status === "Ready"
                            ? "border-emerald-400/15 bg-emerald-400/[0.05] text-emerald-300"
                            : "border-amber-400/15 bg-amber-400/[0.05] text-amber-300"
                        }`}
                      >
                        {payment.status}
                      </span>

                      <span className="text-white/20 transition-all group-hover:translate-x-1 group-hover:text-white/70">
                        →
                      </span>
                    </div>
                  </button>
                ))}
              </div>
            </section>

            {/* FOOTER SIGNAL */}
            <div className="mt-6 flex flex-col justify-between gap-3 text-[10px] text-white/25 sm:flex-row">
              <div>
                AI proposes · Policy protects · Outcomes teach
              </div>

              <div className="flex gap-4">
                <span>500+ payment events</span>
                <span>•</span>
                <span>Razorpay Test Mode</span>
              </div>
            </div>
          </div>
        </section>
      </div>

      {/* PAYMENT DETAIL DRAWER */}
      {selectedPayment && (
        <div
          className="fixed inset-0 z-50 flex justify-end bg-black/60 backdrop-blur-[2px]"
          onClick={() => setSelectedPayment(null)}
        >
          <div
            className="h-full w-full max-w-[460px] border-l border-white/[0.08] bg-[#101112] p-6 shadow-2xl sm:p-8"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="mb-10 flex items-center justify-between">
              <div>
                <div className="text-[10px] uppercase tracking-[0.15em] text-white/25">
                  Recovery case
                </div>
                <div className="mt-1 text-[18px] font-medium">
                  {selectedPayment.payment_id}
                </div>
              </div>

              <button
                onClick={() => setSelectedPayment(null)}
                className="flex h-8 w-8 items-center justify-center rounded-full border border-white/[0.08] text-white/40 hover:text-white"
              >
                ×
              </button>
            </div>

            <div className="mb-8">
              <div className="text-[34px] font-semibold tracking-[-0.04em]">
                {formatMoney(selectedPayment.amount)}
              </div>

              <div className="mt-2 text-[12px] text-white/35">
                {selectedPayment.customer}
              </div>
            </div>

            <div className="space-y-1 border-y border-white/[0.07] py-4">
              <DetailRow
                label="Failure"
                value={selectedPayment.reason ?? "Unknown"}
              />

              <DetailRow
                label="Recovery probability"
                value={
                  aiLoading
                    ? "Analyzing..."
                    : aiRecommendation?.recommendation?.recovery_probability != null
                      ? `${Math.round(
                          aiRecommendation.recommendation.recovery_probability * 100
                        )}%`
                      : selectedPayment.probability !== null
                        ? `${Math.round(selectedPayment.probability * 100)}%`
                        : "Not available"
                }
              />

              <DetailRow
                label="Recommendation"
                value={
                  aiLoading
                    ? "Analyzing..."
                    : aiRecommendation?.recommendation?.recommended_action ??
                      selectedPayment.action ??
                      "Not available"
                }
              />

              <DetailRow
                label="Policy"
                value={
                  aiLoading
                    ? "Evaluating..."
                    : aiRecommendation?.policy?.decision ??
                      selectedPayment.policy_decision ??
                      "Not available"
                }
              />
            </div>

            <div className="mt-8 rounded-xl border border-white/[0.07] bg-white/[0.025] p-5">
              <div className="mb-4 flex items-center gap-2">
                <span className="text-[13px]">✦</span>
                <span className="text-[12px] font-medium">
                  AI decision
                </span>
              </div>

              <div className="space-y-3">
                <div>
                  <div className="text-[9px] uppercase tracking-[0.12em] text-white/25">
                    Diagnosis
                  </div>

                  <p className="mt-1 text-[11px] leading-5 text-white/55">
                    {aiLoading
                      ? "RecoverX is analyzing the payment..."
                      : aiRecommendation?.recommendation?.diagnosis ??
                        "Not available"}
                  </p>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <div className="text-[9px] uppercase tracking-[0.12em] text-white/25">
                      Confidence
                    </div>

                    <div className="mt-1 text-[12px] text-white/65">
                      {aiLoading
                        ? "..."
                        : aiRecommendation?.recommendation?.confidence != null
                          ? `${Math.round(
                              aiRecommendation.recommendation.confidence * 100
                            )}%`
                          : "Not available"}
                    </div>
                  </div>

                  <div>
                    <div className="text-[9px] uppercase tracking-[0.12em] text-white/25">
                      Retry after
                    </div>

                    <div className="mt-1 text-[12px] text-white/65">
                      {aiLoading
                        ? "..."
                        : aiRecommendation?.recommendation?.retry_after_hours != null
                          ? `${aiRecommendation.recommendation.retry_after_hours}h`
                          : "Not applicable"}
                    </div>
                  </div>
                </div>

                <div>
                  <div className="text-[9px] uppercase tracking-[0.12em] text-white/25">
                    Explanation
                  </div>

                  <p className="mt-1 text-[11px] leading-5 text-white/40">
                    {aiLoading
                      ? "RecoverX is evaluating the safest recovery action..."
                      : aiRecommendation?.recommendation?.explanation ??
                        "Not available"}
                  </p>
                </div>
              </div>
            </div>
            {aiRecommendation?.audits?.length > 0 && (
              <div className="mt-6 rounded-xl border border-white/[0.07] bg-white/[0.025] p-5">
                <div className="mb-4 flex items-center justify-between">
                  <div>
                    <div className="text-[12px] font-medium">
                      Audit timeline
                    </div>

                    <div className="mt-1 text-[10px] text-white/25">
                      Every decision is recorded.
                    </div>
                  </div>

                  <span className="text-[9px] uppercase tracking-[0.12em] text-white/20">
                    {aiRecommendation.audits.length} events
                  </span>
                </div>

                <div className="space-y-4">
                  {aiRecommendation.audits.map(
                    (
                      event: {
                        id: number;
                        event_type: string;
                        description: string;
                        timestamp: string;
                      },
                      index: number
                    ) => (
                      <div key={event.id} className="relative pl-5">
                        {index < aiRecommendation.audits.length - 1 && (
                          <div className="absolute left-[3px] top-3 h-full w-px bg-white/[0.08]" />
                        )}

                        <div className="absolute left-0 top-1.5 h-[7px] w-[7px] rounded-full bg-white/60" />

                        <div className="text-[9px] uppercase tracking-[0.1em] text-white/25">
                          {event.event_type.replaceAll("_", " ")}
                        </div>

                        <p className="mt-1 text-[10px] leading-5 text-white/40">
                          {event.description}
                        </p>

                        <div className="mt-1 text-[9px] text-white/20">
                          {new Date(event.timestamp).toLocaleString()}
                        </div>
                      </div>
                    )
                  )}
                </div>
              </div>
            )}
            <div className="mt-6 rounded-xl border border-white/[0.07] bg-white/[0.025] p-5">
              <div className="mb-4 flex items-center gap-2">
                <span className="text-[13px]">✦</span>
                <span className="text-[12px] font-medium">
                  Why RecoverX chose this
                </span>
              </div>

              <p className="text-[11px] leading-5 text-white/40">
                {aiLoading
                  ? "RecoverX is analyzing the payment context and evaluating the best recovery action..."
                  : aiRecommendation?.policy?.reason ??
                    "The recommendation combines payment context, customer reliability, previous attempts and historical recovery experience. The policy engine determines whether the proposed action is allowed."}
              </p>
            </div>

            {selectedPayment.status === "Ready" && (
              <button
                onClick={() => executeRecovery(selectedPayment.recovery_id)}
                disabled={executionLoading}
                className="mt-6 w-full rounded-lg bg-white py-3 text-[12px] font-semibold text-black transition hover:bg-white/90 active:scale-[0.99] disabled:opacity-50"
              >
                {executionLoading ? "Executing..." : "Execute recovery →"}
              </button>
            )}
          </div>
        </div>
      )}
    </main>
  );
}

function Metric({
  label,
  value,
  change,
  positive,
  large = false,
}: {
  label: string;
  value: React.ReactNode;
  change: string;
  positive: boolean;
  large?: boolean;
}) {
  return (
    <div className="group bg-[#101112] p-5 transition-colors hover:bg-[#131516] sm:p-6">
      <div className="mb-5 flex items-center justify-between">
        <span className="text-[10px] uppercase tracking-[0.13em] text-white/30">
          {label}
        </span>

        <span
          className={`text-[10px] ${
            positive ? "text-emerald-300" : "text-white/30"
          }`}
        >
          {change}
        </span>
      </div>

      <div
        className={`font-semibold tracking-[-0.04em] ${
          large ? "text-[29px]" : "text-[24px]"
        }`}
      >
        {value}
      </div>
    </div>
  );
}

function DetailRow({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="flex items-center justify-between py-2.5">
      <span className="text-[10px] text-white/25">{label}</span>
      <span className="max-w-[60%] text-right text-[11px] text-white/65">
        {value}
      </span>
    </div>
  );
}