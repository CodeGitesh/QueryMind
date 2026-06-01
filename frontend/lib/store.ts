// Zustand global state store

import { create } from "zustand";
import { devtools } from "zustand/middleware";
import type { QueryResponse, HistoryItem, SchemaInfo } from "./types";

interface QueryMindState {
  // Active query
  currentQuery: string;
  setCurrentQuery: (q: string) => void;

  // Active schema
  activeSchema: string;
  setActiveSchema: (s: string) => void;

  // Query result
  result: QueryResponse | null;
  setResult: (r: QueryResponse | null) => void;

  // Loading state
  isLoading: boolean;
  setIsLoading: (v: boolean) => void;

  // Streaming steps
  streamSteps: string[];
  addStreamStep: (step: string) => void;
  clearStreamSteps: () => void;

  // Query history (local cache)
  history: HistoryItem[];
  setHistory: (h: HistoryItem[]) => void;
  prependHistory: (item: HistoryItem) => void;

  // Schema browser
  schemaBrowserOpen: boolean;
  toggleSchemaBrowser: () => void;

  // Cached schemas
  schemas: Record<string, SchemaInfo>;
  setSchema: (name: string, schema: SchemaInfo) => void;

  // Uploaded schema name
  uploadedSchema: string | null;
  setUploadedSchema: (s: string | null) => void;

  // Session ID
  sessionId: string;
}

export const useStore = create<QueryMindState>()(
  devtools(
    (set) => ({
      currentQuery: "",
      setCurrentQuery: (q) => set({ currentQuery: q }),

      activeSchema: "ecommerce",
      setActiveSchema: (s) => set({ activeSchema: s }),

      result: null,
      setResult: (r) => set({ result: r }),

      isLoading: false,
      setIsLoading: (v) => set({ isLoading: v }),

      streamSteps: [],
      addStreamStep: (step) =>
        set((state) => ({ streamSteps: [...state.streamSteps, step] })),
      clearStreamSteps: () => set({ streamSteps: [] }),

      history: [],
      setHistory: (h) => set({ history: h }),
      prependHistory: (item) =>
        set((state) => ({ history: [item, ...state.history] })),

      schemaBrowserOpen: true,
      toggleSchemaBrowser: () =>
        set((state) => ({ schemaBrowserOpen: !state.schemaBrowserOpen })),

      schemas: {},
      setSchema: (name, schema) =>
        set((state) => ({ schemas: { ...state.schemas, [name]: schema } })),

      uploadedSchema: null,
      setUploadedSchema: (s) => set({ uploadedSchema: s }),

      sessionId:
        typeof window !== "undefined"
          ? (sessionStorage.getItem("qm_session") ?? crypto.randomUUID())
          : "ssr",
    }),
    { name: "QueryMindStore" }
  )
);
