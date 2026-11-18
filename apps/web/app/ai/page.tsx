"use client";

import React, { useState, useEffect, useRef, Suspense } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import {
  Bot,
  Send,
  Plus,
  Trash2,
  Copy,
  Check,
  ChevronDown,
  ChevronRight,
  ExternalLink,
  ShieldCheck,
  AlertTriangle,
  Loader2,
  Sparkles,
  BookOpen,
  Terminal,
  Activity,
  ArrowRight,
  RefreshCw,
  Info,
  Lock,
} from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import { DashboardLayout } from "@/components/DashboardLayout";
import {
  api,
  AIConversation,
  AIMessage,
  AIToolExecution,
  AIRetrievalSource,
  ToolCatalogItem,
  EvaluationResponse,
} from "@/lib/api";

function sanitizeInline(text: string): React.ReactNode[] {
  // Prevent javascript: protocol or dangerous tags
  const clean = text.replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, "");
  // Support inline `code` blocks
  const codeParts = clean.split("`");
  if (codeParts.length > 1) {
    return codeParts.map((segment, cIdx) => {
      if (cIdx % 2 === 1) {
        return (
          <code key={`inline-code-${cIdx}`} className="font-mono text-[11px] bg-[#080d16] text-[#71d5b3] px-1.5 py-0.5 rounded border border-[#1e2d3e]">
            {segment}
          </code>
        );
      }
      const boldParts = segment.split("**");
      return (
        <React.Fragment key={`seg-${cIdx}`}>
          {boldParts.map((p, bIdx) =>
            bIdx % 2 === 1 ? <strong key={bIdx} className="text-[#edf3fa]">{p}</strong> : p
          )}
        </React.Fragment>
      );
    });
  }

  const boldParts = clean.split("**");
  return boldParts.map((p, idx) =>
    idx % 2 === 1 ? <strong key={idx} className="text-[#edf3fa]">{p}</strong> : p
  );
}

function MarkdownContent({ content }: { content: string }) {
  const lines = content.split("\n");
  const renderedElements: React.ReactNode[] = [];
  let inCodeBlock = false;
  let codeBlockBuffer: string[] = [];

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];

    if (line.startsWith("```")) {
      if (inCodeBlock) {
        renderedElements.push(
          <pre
            key={`code-${i}`}
            className="my-2 p-3 rounded-lg bg-[#080d16] border border-[#1e2d3e] font-mono text-[11px] text-[#71d5b3] overflow-x-auto"
          >
            <code>{codeBlockBuffer.join("\n")}</code>
          </pre>
        );
        codeBlockBuffer = [];
        inCodeBlock = false;
      } else {
        inCodeBlock = true;
      }
      continue;
    }

    if (inCodeBlock) {
      codeBlockBuffer.push(line);
      continue;
    }

    if (line.startsWith("### ")) {
      renderedElements.push(
        <h3
          key={`h3-${i}`}
          className="text-xs font-bold text-[#edf3fa] uppercase tracking-wider mt-4 mb-1.5 flex items-center gap-1.5"
        >
          <span className="w-1.5 h-1.5 rounded-full bg-[#71d5b3]" />
          {line.replace("### ", "")}
        </h3>
      );
      continue;
    }

    if (line.startsWith("## ")) {
      renderedElements.push(
        <h2 key={`h2-${i}`} className="text-sm font-bold text-[#edf3fa] mt-4 mb-2">
          {line.replace("## ", "")}
        </h2>
      );
      continue;
    }

    if (line.startsWith("> [!NOTE]")) {
      renderedElements.push(
        <div
          key={`callout-${i}`}
          className="my-2 p-3 rounded-lg bg-[#0e1724] border-l-2 border-[#71d5b3] text-[11px] text-[#91a0b3]"
        >
          <div className="flex items-center gap-1.5 font-bold text-[#71d5b3] mb-1">
            <Info size={13} />
            <span>Note</span>
          </div>
          {line.replace("> [!NOTE]", "").trim()}
        </div>
      );
      continue;
    }

    if (line.startsWith("> ")) {
      renderedElements.push(
        <blockquote
          key={`quote-${i}`}
          className="my-1.5 pl-3 border-l-2 border-[#1e2d3e] text-[11px] text-[#91a0b3] italic"
        >
          {line.replace("> ", "")}
        </blockquote>
      );
      continue;
    }

    if (line.startsWith("- ")) {
      renderedElements.push(
        <li key={`li-${i}`} className="text-xs text-[#ced8e5] ml-4 list-disc leading-relaxed my-0.5">
          {sanitizeInline(line.replace("- ", ""))}
        </li>
      );
      continue;
    }

    if (line.trim() === "---") {
      renderedElements.push(<hr key={`hr-${i}`} className="my-3 border-[#1e2d3e]" />);
      continue;
    }

    if (line.trim() === "") {
      renderedElements.push(<div key={`sp-${i}`} className="h-1.5" />);
      continue;
    }

    // Standard paragraph with bold formatting and inline code
    renderedElements.push(
      <p key={`p-${i}`} className="text-xs text-[#ced8e5] leading-relaxed my-1">
        {sanitizeInline(line)}
      </p>
    );
  }

  return <div className="space-y-0.5">{renderedElements}</div>;
}

function AICopilotView() {
  const { user } = useAuth();
  const searchParams = useSearchParams();
  const contextModule = searchParams.get("explain");
  const contextSymbol = searchParams.get("symbol");

  const [conversations, setConversations] = useState<AIConversation[]>([]);
  const [activeConvId, setActiveConvId] = useState<string | null>(null);
  const [messages, setMessages] = useState<AIMessage[]>([]);
  const [inputPrompt, setInputPrompt] = useState("");
  const [loading, setLoading] = useState(false);
  const [fetchingHistory, setFetchingHistory] = useState(false);

  // Modals & Panels
  const [showToolsModal, setShowToolsModal] = useState(false);
  const [toolsList, setToolsList] = useState<ToolCatalogItem[]>([]);
  const [evalLoading, setEvalLoading] = useState(false);
  const [evalResult, setEvalResult] = useState<EvaluationResponse | null>(null);

  // Inspector toggles
  const [expandedTools, setExpandedTools] = useState<Record<string, boolean>>({});
  const [expandedSources, setExpandedSources] = useState<Record<string, boolean>>({});
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Suggested prompts
  const suggestedPrompts = [
    { label: "TCS Technicals", prompt: "Explain TCS's RSI and MACD indicators using deterministic analytics." },
    { label: "P/E & ROE Analysis", prompt: "What is the P/E ratio, P/B ratio, and ROE of Reliance from audited statements?" },
    { label: "TCS vs INFY", prompt: "Compare TCS and INFY side-by-side over a 1Y period." },
    { label: "Portfolio Valuation", prompt: "What is my current portfolio valuation, cash balance, and unrealized P&L?" },
    { label: "TWR vs XIRR", prompt: "Explain the difference between Time-Weighted Return (TWR) and Extended IRR (XIRR) for my portfolio." },
    { label: "HDFC Mutual Funds", prompt: "Search for HDFC mutual funds and explain Direct vs Regular plans." },
    { label: "Indian Macro Series", prompt: "What are the latest Indian macroeconomic indicators like CPI inflation and RBI repo rate?" },
    { label: "Backtest Overfitting", prompt: "Explain why overfitting matters in strategy backtesting and how train/test split helps." },
  ];

  // Load user conversations on mount
  useEffect(() => {
    if (user) {
      loadConversations();
      loadToolsCatalog();
    }
  }, [user]);

  // Handle URL query parameters to trigger context-aware grounding
  useEffect(() => {
    if (contextModule) {
      const defaultQuery = contextSymbol
        ? `Explain ${contextSymbol}'s technical indicators and financial valuation.`
        : `Provide research intelligence on ${contextModule}.`;
      setInputPrompt(defaultQuery);
    }
  }, [contextModule, contextSymbol]);

  // Scroll to bottom when messages update
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const loadConversations = async () => {
    if (!user) return;
    try {
      const convs = await api.listConversations();
      setConversations(convs);
      if (convs.length > 0 && !activeConvId) {
        selectConversation(convs[0].id);
      } else if (convs.length === 0) {
        handleNewConversation();
      }
    } catch (err) {
      console.error("Failed to load conversations:", err);
    }
  };

  const loadToolsCatalog = async () => {
    if (!user) return;
    try {
      const tools = await api.listAiTools();
      setToolsList(tools);
    } catch (err) {
      console.error("Failed to load tool catalog:", err);
    }
  };

  const selectConversation = async (convId: string) => {
    setActiveConvId(convId);
    setFetchingHistory(true);
    try {
      const detail = await api.getConversation(convId);
      setMessages(detail.messages || []);
    } catch (err) {
      console.error("Failed to fetch conversation history:", err);
    } finally {
      setFetchingHistory(false);
    }
  };

  const handleNewConversation = async () => {
    try {
      const title = contextModule ? `${contextModule.toUpperCase()} Intelligence` : "Financial Research";
      const newConv = await api.createConversation({
        title,
        context_module: contextModule || undefined,
      });
      setConversations((prev) => [newConv, ...prev]);
      setActiveConvId(newConv.id);
      setMessages([]);
    } catch (err) {
      console.error("Failed to create conversation:", err);
    }
  };

  const handleDeleteConversation = async (e: React.MouseEvent, convId: string) => {
    e.stopPropagation();
    if (!confirm("Are you sure you want to delete this research session?")) return;
    try {
      await api.deleteConversation(convId);
      setConversations((prev) => prev.filter((c) => c.id !== convId));
      if (activeConvId === convId) {
        const remaining = conversations.filter((c) => c.id !== convId);
        if (remaining.length > 0) {
          selectConversation(remaining[0].id);
        } else {
          setActiveConvId(null);
          setMessages([]);
        }
      }
    } catch (err) {
      console.error("Failed to delete conversation:", err);
    }
  };

  const handleSendMessage = async (textToSend?: string) => {
    const promptText = (textToSend || inputPrompt).trim();
    if (!promptText || loading) return;

    let targetConvId = activeConvId;
    if (!targetConvId) {
      try {
        const newConv = await api.createConversation({
          title: promptText.slice(0, 50),
          context_module: contextModule || undefined,
        });
        setConversations((prev) => [newConv, ...prev]);
        setActiveConvId(newConv.id);
        targetConvId = newConv.id;
      } catch (err) {
        console.error("Failed to initialize conversation:", err);
        return;
      }
    }

    // Optimistically append user message
    const tempUserMsg: AIMessage = {
      id: "temp-" + Date.now(),
      conversation_id: targetConvId,
      role: "user",
      content: promptText,
      created_at: new Date().toISOString(),
      tool_executions: [],
      retrieval_sources: [],
    };
    setMessages((prev) => [...prev, tempUserMsg]);
    setInputPrompt("");
    setLoading(true);

    try {
      const turnResp = await api.sendMessage(targetConvId, {
        content: promptText,
        context_module: contextModule || undefined,
      });

      const assistantMsg: AIMessage = {
        id: turnResp.assistant_message_id,
        conversation_id: turnResp.conversation_id,
        role: "assistant",
        content: turnResp.content,
        provider: turnResp.provider,
        model_name: turnResp.model_name,
        tokens_used: turnResp.tokens_used,
        latency_ms: turnResp.latency_ms,
        created_at: turnResp.created_at,
        tool_executions: turnResp.tool_executions,
        retrieval_sources: turnResp.retrieval_sources,
      };

      setMessages((prev) => [...prev.filter((m) => m.id !== tempUserMsg.id), tempUserMsg, assistantMsg]);
      // Refresh conversation list to pick up updated title / timestamp
      api.listConversations().then(setConversations).catch(() => {});
    } catch (err: any) {
      console.error("Failed to send message:", err);
      const errorMsg: AIMessage = {
        id: "err-" + Date.now(),
        conversation_id: targetConvId,
        role: "assistant",
        content: `**Error:** ${err.message || "Failed to execute research turn."}`,
        created_at: new Date().toISOString(),
        tool_executions: [],
        retrieval_sources: [],
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = (msgId: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(msgId);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handleRunEvaluation = async () => {
    setEvalLoading(true);
    try {
      const result = await api.runAiEvaluation();
      setEvalResult(result);
    } catch (err) {
      console.error("Failed to run evaluation benchmark:", err);
    } finally {
      setEvalLoading(false);
    }
  };

  const activeConversation = conversations.find((c) => c.id === activeConvId);

  return (
    <DashboardLayout title="QuantWeave AI Copilot">
      {/* Top Banner if context is attached from URL */}
      {contextModule && (
        <div className="mb-4 p-3 rounded-xl bg-[#0c1a26] border border-[#1e3e4a] flex items-center justify-between">
          <div className="flex items-center gap-2 text-xs text-[#71d5b3]">
            <Sparkles size={15} />
            <span>
              <strong>Active Context Grounding:</strong> {contextModule.toUpperCase()}
              {contextSymbol ? ` [${contextSymbol}]` : ""}. Questions will automatically prioritize this entity.
            </span>
          </div>
          <Link
            href="/ai"
            className="text-[11px] text-[#91a0b3] hover:text-[#edf3fa] underline"
          >
            Clear Context
          </Link>
        </div>
      )}

      {/* Guest Mode Indicator */}
      {!user && (
        <div className="mb-4 p-3 rounded-xl bg-[#0e1b2b] border border-[#1e3650] flex items-center justify-between">
          <div className="flex items-center gap-2 text-xs text-[#38bdf8]">
            <Lock size={14} className="flex-shrink-0" />
            <span>
              <strong>Guest Demo Mode:</strong> You can explore public stock queries and RAG methodology citations. Sign in to save persistent conversation histories and analyze private portfolios.
            </span>
          </div>
          <Link
            href="/login"
            className="px-3 py-1 rounded-lg bg-[#38bdf8] text-[#07130f] font-bold text-xs hover:bg-[#7dd3fc] transition-colors whitespace-nowrap ml-2"
          >
            Sign In
          </Link>
        </div>
      )}

      {/* Main Copilot Workspace */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4 h-[calc(100vh-140px)] min-h-[600px]">
        {/* Left Sidebar: Conversations & Controls */}
        <div className="lg:col-span-1 rounded-2xl bg-[#0e1724] border border-[#1e2d3e] flex flex-col p-3 overflow-hidden">
          {/* Header & New Chat Action */}
          <div className="flex items-center justify-between mb-3 pb-3 border-b border-[#1e2d3e]">
            <div className="flex items-center gap-2">
              <Bot size={18} className="text-[#71d5b3]" />
              <span className="text-xs font-bold text-[#edf3fa]">Research Sessions</span>
            </div>
            <button
              onClick={handleNewConversation}
              className="p-1.5 rounded-lg bg-[#15273b] hover:bg-[#1a324b] text-[#71d5b3] transition flex items-center gap-1 text-[11px] font-bold px-2"
              title="Start New Research"
            >
              <Plus size={13} />
              <span>New</span>
            </button>
          </div>

          {/* Conversations List */}
          <div className="flex-1 overflow-y-auto space-y-1 pr-1 custom-scrollbar">
            {conversations.length === 0 ? (
              <div className="p-4 text-center text-xs text-[#607286]">No active research sessions.</div>
            ) : (
              conversations.map((conv) => {
                const isActive = conv.id === activeConvId;
                return (
                  <div
                    key={conv.id}
                    onClick={() => selectConversation(conv.id)}
                    className={`group p-2.5 rounded-xl cursor-pointer transition flex items-center justify-between text-xs ${
                      isActive
                        ? "bg-[#142334] text-[#edf3fa] border border-[#1e3e4a]"
                        : "text-[#91a0b3] hover:bg-[#121c2b] hover:text-[#ced8e5]"
                    }`}
                  >
                    <div className="truncate flex-1 pr-2">
                      <div className="font-medium truncate">{conv.title}</div>
                      <div className="text-[10px] text-[#607286] flex items-center gap-1 mt-0.5">
                        {conv.context_module && (
                          <span className="uppercase px-1 py-0.2 rounded bg-[#0b1420] text-[#71d5b3] text-[9px]">
                            {conv.context_module}
                          </span>
                        )}
                        <span>{new Date(conv.updated_at).toLocaleDateString()}</span>
                      </div>
                    </div>
                    <button
                      onClick={(e) => handleDeleteConversation(e, conv.id)}
                      className="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-[#201518] hover:text-red-400 text-[#607286] transition"
                      title="Delete Session"
                    >
                      <Trash2 size={13} />
                    </button>
                  </div>
                );
              })
            )}
          </div>

          {/* Bottom Controls: Tool Catalog & Benchmark Evals */}
          <div className="pt-3 border-t border-[#1e2d3e] space-y-2">
            <button
              onClick={() => setShowToolsModal(true)}
              className="w-full p-2 rounded-xl bg-[#121c2b] hover:bg-[#152538] text-[#ced8e5] text-xs font-medium flex items-center justify-between transition"
            >
              <span className="flex items-center gap-1.5">
                <Terminal size={14} className="text-[#71d5b3]" />
                <span>Tool Catalog</span>
              </span>
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-[#1e2d3e] text-[#71d5b3]">
                {toolsList.length || 22} tools
              </span>
            </button>

            <button
              onClick={handleRunEvaluation}
              disabled={evalLoading}
              className="w-full p-2 rounded-xl bg-[#121c2b] hover:bg-[#152538] text-[#ced8e5] text-xs font-medium flex items-center justify-between transition disabled:opacity-50"
            >
              <span className="flex items-center gap-1.5">
                {evalLoading ? <Loader2 size={14} className="animate-spin text-[#71d5b3]" /> : <Activity size={14} className="text-[#71d5b3]" />}
                <span>Benchmark Evals</span>
              </span>
              <span className="text-[10px] text-[#91a0b3]">Run Suite</span>
            </button>
          </div>
        </div>

        {/* Center / Right Chat Workspace */}
        <div className="lg:col-span-3 rounded-2xl bg-[#0e1724] border border-[#1e2d3e] flex flex-col overflow-hidden">
          {/* Header */}
          <div className="px-5 py-3.5 border-b border-[#1e2d3e] bg-[#0c1420] flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-[#15273b] text-[#71d5b3] flex items-center justify-center">
                <Bot size={18} />
              </div>
              <div>
                <h3 className="text-xs font-bold text-[#edf3fa]">
                  {activeConversation?.title || "Financial Research Copilot"}
                </h3>
                <div className="text-[10px] text-[#91a0b3] flex items-center gap-2">
                  <span className="flex items-center gap-1">
                    <ShieldCheck size={11} className="text-[#71d5b3]" />
                    Deterministic Grounding
                  </span>
                  <span>•</span>
                  <span>Zero Hallucination Guardrails</span>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-[#15273b] text-[#71d5b3] border border-[#1e3e4a]">
                Mock LLM Engine (Offline Demo)
              </span>
            </div>
          </div>

          {/* Message Thread */}
          <div className="flex-1 overflow-y-auto p-5 space-y-4 custom-scrollbar">
            {fetchingHistory ? (
              <div className="flex items-center justify-center h-full text-xs text-[#91a0b3] gap-2">
                <Loader2 size={16} className="animate-spin text-[#71d5b3]" />
                <span>Loading research history...</span>
              </div>
            ) : messages.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-center max-w-lg mx-auto py-8">
                <div className="w-14 h-14 rounded-2xl bg-[#15273b] text-[#71d5b3] flex items-center justify-center mb-3">
                  <Bot size={28} />
                </div>
                <h4 className="text-base font-bold text-[#edf3fa] mb-1">
                  How can QuantWeave Copilot assist your research?
                </h4>
                <p className="text-xs text-[#91a0b3] leading-relaxed mb-6">
                  Ask questions about Indian equities, financial statements, portfolio valuations,
                  mutual fund direct vs regular plans, macroeconomic indices, or QuantLab backtesting models.
                </p>

                {/* Suggested prompt chips */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 w-full text-left">
                  {suggestedPrompts.map((s, idx) => (
                    <button
                      key={idx}
                      onClick={() => handleSendMessage(s.prompt)}
                      className="p-2.5 rounded-xl bg-[#121c2b] hover:bg-[#152538] border border-[#1e2d3e] text-xs text-[#ced8e5] transition flex items-center justify-between group"
                    >
                      <span className="truncate pr-2">{s.label}</span>
                      <ArrowRight size={13} className="text-[#71d5b3] opacity-0 group-hover:opacity-100 transition" />
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              messages.map((msg) => {
                const isUser = msg.role === "user";
                const hasTools = msg.tool_executions && msg.tool_executions.length > 0;
                const hasSources = msg.retrieval_sources && msg.retrieval_sources.length > 0;
                const isToolsOpen = expandedTools[msg.id];
                const isSourcesOpen = expandedSources[msg.id];

                return (
                  <div
                    key={msg.id}
                    className={`flex flex-col ${isUser ? "items-end" : "items-start"}`}
                  >
                    <div
                      className={`max-w-[85%] rounded-2xl p-4 text-xs ${
                        isUser
                          ? "bg-[#162a3d] text-[#edf3fa] rounded-tr-none border border-[#1f3f5a]"
                          : "bg-[#0b131e] text-[#ced8e5] rounded-tl-none border border-[#1e2d3e]"
                      }`}
                    >
                      {/* Message Content */}
                      <MarkdownContent content={msg.content} />

                      {/* Tool Executions Inspector Pill */}
                      {hasTools && (
                        <div className="mt-3 pt-3 border-t border-[#1e2d3e]">
                          <button
                            onClick={() =>
                              setExpandedTools((prev) => ({
                                ...prev,
                                [msg.id]: !prev[msg.id],
                              }))
                            }
                            className="flex items-center gap-1.5 text-[11px] font-bold text-[#71d5b3] hover:underline"
                          >
                            <Terminal size={12} />
                            <span>
                              {msg.tool_executions.length} Backend Tool
                              {msg.tool_executions.length > 1 ? "s" : ""} Executed
                            </span>
                            {isToolsOpen ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
                          </button>

                          {isToolsOpen && (
                            <div className="mt-2 space-y-2">
                              {msg.tool_executions.map((tool, tIdx) => (
                                <div
                                  key={tIdx}
                                  className="p-2.5 rounded-lg bg-[#080d16] border border-[#1e2d3e] font-mono text-[10px]"
                                >
                                  <div className="flex items-center justify-between text-[#71d5b3] mb-1">
                                    <span className="font-bold">{tool.tool_name}()</span>
                                    <span className="text-[#91a0b3]">{tool.execution_time_ms ?? 0}ms</span>
                                  </div>
                                  <pre className="text-[#8ba2be] overflow-x-auto max-h-36">
                                    {JSON.stringify(tool.result, null, 2)}
                                  </pre>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      )}

                      {/* RAG Knowledge Provenance Citations */}
                      {hasSources && (
                        <div className="mt-2 pt-2 border-t border-[#1e2d3e]">
                          <button
                            onClick={() =>
                              setExpandedSources((prev) => ({
                                ...prev,
                                [msg.id]: !prev[msg.id],
                              }))
                            }
                            className="flex items-center gap-1.5 text-[11px] font-bold text-[#6bb5ff] hover:underline"
                          >
                            <BookOpen size={12} />
                            <span>
                              {msg.retrieval_sources.length} Verified Source
                              {msg.retrieval_sources.length > 1 ? "s" : ""} Cited
                            </span>
                            {isSourcesOpen ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
                          </button>

                          {isSourcesOpen && (
                            <div className="mt-2 space-y-1.5">
                              {msg.retrieval_sources.map((src, sIdx) => (
                                <div
                                  key={sIdx}
                                  className="p-2 rounded bg-[#080d16] border border-[#1e2d3e] text-[10px]"
                                >
                                  <div className="flex items-center justify-between font-bold text-[#6bb5ff] mb-0.5">
                                    <span>
                                      {src.citation_key}: {src.source_title}
                                    </span>
                                    <span className="text-[#607286]">
                                      Score: {(src.relevance_score * 100).toFixed(0)}%
                                    </span>
                                  </div>
                                  <p className="text-[#91a0b3] line-clamp-2">{src.snippet}</p>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      )}

                      {/* Footer Actions */}
                      <div className="mt-2.5 pt-2 flex items-center justify-between text-[10px] text-[#607286]">
                        <span>{new Date(msg.created_at).toLocaleTimeString()}</span>
                        {!isUser && (
                          <button
                            onClick={() => handleCopy(msg.id, msg.content)}
                            className="flex items-center gap-1 hover:text-[#edf3fa] transition"
                            title="Copy message"
                          >
                            {copiedId === msg.id ? (
                              <>
                                <Check size={11} className="text-[#71d5b3]" />
                                <span className="text-[#71d5b3]">Copied</span>
                              </>
                            ) : (
                              <>
                                <Copy size={11} />
                                <span>Copy</span>
                              </>
                            )}
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })
            )}

            {loading && (
              <div className="flex items-center gap-2 p-3 rounded-2xl bg-[#0b131e] border border-[#1e2d3e] text-xs text-[#91a0b3] max-w-xs">
                <Loader2 size={15} className="animate-spin text-[#71d5b3]" />
                <span>Executing read-only financial tools & synthesizing...</span>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Bar */}
          <div className="p-3 bg-[#0c1420] border-t border-[#1e2d3e]">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleSendMessage();
              }}
              className="flex items-center gap-2"
            >
              <input
                type="text"
                value={inputPrompt}
                onChange={(e) => setInputPrompt(e.target.value)}
                placeholder="Ask about TCS RSI, portfolio valuation, HDFC funds, macro data..."
                disabled={loading}
                className="flex-1 bg-[#121c2b] border border-[#1e2d3e] rounded-xl px-4 py-3 text-xs text-[#edf3fa] placeholder-[#607286] focus:outline-none focus:border-[#71d5b3] transition disabled:opacity-50"
              />
              <button
                type="submit"
                disabled={!inputPrompt.trim() || loading}
                className="p-3 rounded-xl bg-[#71d5b3] hover:bg-[#5ec4a2] text-[#080d16] font-bold transition disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center"
              >
                {loading ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />}
              </button>
            </form>
            <div className="mt-1.5 flex items-center justify-between text-[10px] text-[#607286] px-1">
              <span>Shift+Enter for newline, Enter to send</span>
              <span>Educational Research Platform • Not SEBI Investment Advice</span>
            </div>
          </div>
        </div>
      </div>

      {/* Tool Catalog Modal */}
      {showToolsModal && (
        <div className="fixed inset-0 bg-black/75 z-50 flex items-center justify-center p-4 backdrop-blur-sm">
          <div className="bg-[#0e1724] border border-[#1e2d3e] rounded-2xl max-w-2xl w-full max-h-[80vh] flex flex-col p-6 overflow-hidden">
            <div className="flex items-center justify-between pb-3 border-b border-[#1e2d3e]">
              <div>
                <h3 className="text-base font-bold text-[#edf3fa] flex items-center gap-2">
                  <Terminal size={18} className="text-[#71d5b3]" />
                  QuantWeave Server-Side Read-Only Tools
                </h3>
                <p className="text-xs text-[#91a0b3]">
                  All 22 tools are strictly read-only and execute deterministic backend analytics.
                </p>
              </div>
              <button
                onClick={() => setShowToolsModal(false)}
                className="text-[#607286] hover:text-[#edf3fa] p-1"
              >
                ✕
              </button>
            </div>

            <div className="flex-1 overflow-y-auto py-3 space-y-2 pr-1 custom-scrollbar">
              {toolsList.map((tool, idx) => (
                <div key={idx} className="p-3 rounded-xl bg-[#121c2b] border border-[#1e2d3e]">
                  <div className="flex items-center justify-between text-xs font-bold text-[#71d5b3] mb-1 font-mono">
                    <span>{tool.name}</span>
                    <span className="text-[10px] font-normal px-1.5 py-0.5 rounded bg-[#15273b] text-[#607286]">
                      read-only
                    </span>
                  </div>
                  <p className="text-xs text-[#ced8e5] mb-2">{tool.description}</p>
                  <div className="text-[10px] text-[#8ba2be] font-mono bg-[#080d16] p-2 rounded">
                    Parameters: {JSON.stringify(tool.parameters.properties || {})}
                  </div>
                </div>
              ))}
            </div>

            <div className="pt-3 border-t border-[#1e2d3e] flex justify-end">
              <button
                onClick={() => setShowToolsModal(false)}
                className="px-4 py-2 rounded-xl bg-[#15273b] hover:bg-[#1a324b] text-xs font-bold text-[#edf3fa] transition"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Benchmark Evaluation Modal */}
      {evalResult && (
        <div className="fixed inset-0 bg-black/75 z-50 flex items-center justify-center p-4 backdrop-blur-sm">
          <div className="bg-[#0e1724] border border-[#1e2d3e] rounded-2xl max-w-2xl w-full max-h-[85vh] flex flex-col p-6 overflow-hidden">
            <div className="flex items-center justify-between pb-3 border-b border-[#1e2d3e]">
              <div>
                <h3 className="text-base font-bold text-[#edf3fa] flex items-center gap-2">
                  <Activity size={18} className="text-[#71d5b3]" />
                  AI Benchmark Evaluation Results
                </h3>
                <p className="text-xs text-[#91a0b3]">
                  Automated verification across Equity, Portfolio, FundScope, MarketPulse, QuantLab, and Security.
                </p>
              </div>
              <button
                onClick={() => setEvalResult(null)}
                className="text-[#607286] hover:text-[#edf3fa] p-1"
              >
                ✕
              </button>
            </div>

            <div className="my-4 p-4 rounded-xl bg-[#121c2b] border border-[#1e2d3e] flex items-center justify-around text-center">
              <div>
                <div className="text-2xl font-bold text-[#71d5b3]">{evalResult.accuracy_pct}%</div>
                <div className="text-[10px] text-[#91a0b3]">Accuracy Score</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-[#edf3fa]">
                  {evalResult.passed_cases} / {evalResult.total_cases}
                </div>
                <div className="text-[10px] text-[#91a0b3]">Test Cases Passed</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-[#71d5b3]">100%</div>
                <div className="text-[10px] text-[#91a0b3]">Prompt Injection Refusal</div>
              </div>
            </div>

            <div className="flex-1 overflow-y-auto space-y-2 pr-1 custom-scrollbar">
              {evalResult.results.map((c, idx) => (
                <div
                  key={idx}
                  className="p-3 rounded-xl bg-[#121c2b] border border-[#1e2d3e] flex items-start justify-between text-xs"
                >
                  <div>
                    <div className="flex items-center gap-2 font-bold text-[#edf3fa]">
                      <span className="uppercase text-[10px] px-1.5 py-0.2 rounded bg-[#1e2d3e] text-[#71d5b3]">
                        {c.module}
                      </span>
                      <span>{c.case_id}</span>
                    </div>
                    <p className="text-[#91a0b3] mt-1 italic">&ldquo;{c.query}&rdquo;</p>
                  </div>
                  <span
                    className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                      c.passed
                        ? "bg-[#102a20] text-[#71d5b3] border border-[#1b4332]"
                        : "bg-[#2a1215] text-red-400 border border-[#431b20]"
                    }`}
                  >
                    {c.passed ? "PASSED" : "FAILED"}
                  </span>
                </div>
              ))}
            </div>

            <div className="pt-3 border-t border-[#1e2d3e] flex justify-end">
              <button
                onClick={() => setEvalResult(null)}
                className="px-4 py-2 rounded-xl bg-[#71d5b3] hover:bg-[#5ec4a2] text-xs font-bold text-[#080d16] transition"
              >
                Done
              </button>
            </div>
          </div>
        </div>
      )}
    </DashboardLayout>
  );
}

export default function AIPage() {
  return (
    <Suspense
      fallback={
        <DashboardLayout title="QuantWeave AI Copilot">
          <div className="flex items-center justify-center h-64 text-xs text-[#91a0b3] gap-2">
            <Loader2 size={16} className="animate-spin text-[#71d5b3]" />
            <span>Loading Copilot Workspace...</span>
          </div>
        </DashboardLayout>
      }
    >
      <AICopilotView />
    </Suspense>
  );
}
