import { useEffect, useState } from "react";
import axios from "axios";
import "./App.css";

const api = axios.create({
    baseURL: (import.meta.env.VITE_API_URL || "http://localhost:2000/api"),
    timeout: 30000,
});
const examples = {
    Hello: 'print("Hello World")',
    Loop: "for i in range(1, 6):\n    print(i)",
    Factorial:
        "def factorial(n: int) -> int:\n    if n <= 1:\n        return 1\n    return n * factorial(n - 1)\n\nprint(factorial(5))",
    Sorting:
        "arr = list(map(int, input().split()))\narr.sort()\nprint(sum(arr))",
};
const errorText = (e) =>
    e.response?.data?.message || e.response?.data?.error || e.message;

function Editor({ title, language, code, onChange }) {
    return (
        <section className="editor-panel">
            <div className="panel-heading">
                <strong>{title}</strong>
                <span className="language-tag">{language}</span>
            </div>
            <div className="editor-area">
                <textarea
                    spellCheck={false}
                    aria-label={title}
                    value={code}
                    onChange={
                        onChange ? (e) => onChange(e.target.value) : undefined
                    }
                    readOnly={!onChange}
                    placeholder={
                        onChange
                            ? "Enter Python code..."
                            : "Converted C++ appears here..."
                    }
                />
            </div>
            <div className="panel-footer">
                {code.split("\n").length} lines Â· {code.length} characters
            </div>
        </section>
    );
}

function formatCppForDisplay(code) {
    if (!code) return "";

    let formatted = code.replace(/\bstd::(?=[A-Za-z_])/g, "");

    if (!formatted.includes("using namespace std;")) {
        const lines = formatted.split("\n");
        let index = 0;

        lines.forEach((line, i) => {
            if (line.trim().startsWith("#include")) {
                index = i + 1;
            }
        });

        lines.splice(index, 0, "using namespace std;");
        formatted = lines.join("\n");
    }

    return formatted;
}

export default function App() {
    const [sourceCode, setSourceCode] = useState(examples.Hello);
    const [stdin, setStdin] = useState("");
    const [convertedCode, setConvertedCode] = useState("");
    const [migrationId, setMigrationId] = useState(null);
    const [ollamaCode, setOllamaCode] = useState("");
    const [tripleResult, setTripleResult] = useState(null);

    const [example, setExample] = useState("Hello");
    const [busy, setBusy] = useState("");
    const [notice, setNotice] = useState(null);
    const [output, setOutput] = useState("");
    const [history, setHistory] = useState([]);
    const [historyOpen, setHistoryOpen] = useState(false);
    const [historyError, setHistoryError] = useState("");
    const [search, setSearch] = useState("");
    const [activeId, setActiveId] = useState(null);

    async function loadHistory() {
        try {
            const { data } = await api.get("/history");
            const entries = Array.isArray(data)
                ? data
                : (data.history ??
                  data.migrations ??
                  data.data ??
                  data.results ??
                  []);
            setHistory(Array.isArray(entries) ? entries : []);
            setHistoryError("");
        } catch (e) {
            setHistoryError(
    e.response?.status === 403
        ? "History is temporarily disabled for security"
        : errorText(e)
);
        }
    }

    useEffect(() => {
        loadHistory();
    }, []);

    function openHistory(item) {
        setSourceCode(item.sourceCode ?? item.pythonCode ?? "");
        setConvertedCode(item.convertedCode ?? item.cppCode ?? "");
        setMigrationId(item._id ?? item.migrationId ?? null);
        setOutput("");
        setNotice(null);
        setHistoryOpen(false);
        setActiveId(item._id ?? item.id ?? null);
    }

    const resetResult = () => {
        setOllamaCode("");
        setTripleResult(null);

        setConvertedCode("");
        setMigrationId(null);
        setOutput("");
        setNotice(null);
    };
    const notify = (type, text) => setNotice({ type, text });

    async function convert() {
        if (!sourceCode.trim())
            return notify("error", "Enter Python code first.");
        setBusy("convert");
        resetResult();
        try {
            const { data } = await api.post("/migration/convert", {
                sourceCode,
                stdin,
                sourceLanguage: "python",
                targetLanguage: "cpp",
            });
            if (data.success === false)
                throw Error(data.message || "Conversion failed");
            setConvertedCode(data.convertedCode || "");
            setOllamaCode(data.ollamaCode || "");
            setTripleResult({
                validated: data.validated,
                pythonOutput: data.pythonOutput,
                astOutput: data.astOutput,
                ollamaOutput: data.ollamaOutput,
            });

            setMigrationId(data.migrationId || null);
            setActiveId(data.migrationId || null);
            notify(
                "success",
                `Converted successfully${data.method ? ` Â· ${data.method}` : ""}`,
            );
            await loadHistory();
        } catch (e) {
            notify("error", errorText(e));
        } finally {
            setBusy("");
        }
    }

    async function validate() {
        if (!convertedCode) return;
        setBusy("validate");
        setOutput("");
        setNotice(null);
        try {
            const { data } = await api.post("/validation/check", {
                code: convertedCode,
                language: "cpp",
            });
            if (data.success === false)
                throw Error(data.message || "Validation failed");
            setOutput(data.output ?? data.executionOutput ?? data.stdout ?? "");
            notify("success", data.message || "C++ validated successfully.");
            await loadHistory();
        } catch (e) {
            notify("error", errorText(e));
        } finally {
            setBusy("");
        }
    }

    function download() {
        const url = URL.createObjectURL(
            new Blob([convertedCode], { type: "text/plain" }),
        );
        const link = document.createElement("a");
        link.href = url;
        link.download = "converted.cpp";
        link.click();
        setTimeout(() => URL.revokeObjectURL(url), 1000);
    }

    async function copy() {
        try {
            await navigator.clipboard.writeText(convertedCode);
            notify("success", "C++ code copied.");
        } catch {
            notify("error", "Copy failed.");
        }
    }

    return (
        <div className="app-shell">
            <header className="topbar">
                <strong>
                    <span>AI</span> Powered Code Migration System
                </strong>
                <small>Python to C++17</small>
            </header>

            <button
                className="history-mobile-toggle"
                onClick={() => setHistoryOpen(!historyOpen)}
            >
                {historyOpen ? "âœ• Close" : "â˜° History"}
            </button>
            {historyOpen && (
                <button
                    className="sidebar-backdrop"
                    aria-label="Close sidebar"
                    onClick={() => setHistoryOpen(false)}
                />
            )}
            <div className="app-layout">
                <aside
                    className={`history-sidebar ${historyOpen ? "open" : ""}`}
                    aria-label="Conversion history"
                >
                    <button
                        className="new-conversion"
                        onClick={() => {
                            setSourceCode("");
                            resetResult();
                            setActiveId(null);
                            setHistoryOpen(false);
                        }}
                    >
                        ï¼‹ New Conversion
                    </button>
                    <div className="history-head">
                        <strong>â—· &nbsp; Conversion History</strong>
                        <button
                            onClick={loadHistory}
                            title="Refresh history"
                            aria-label="Refresh history"
                        >
                            â†»
                        </button>
                    </div>
                    <input
                        className="history-search"
                        aria-label="Search conversions"
                        placeholder="âŒ•  Search conversions..."
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                    />
                    {historyError && (
                        <p className="history-error">{historyError}</p>
                    )}
                    {!history.length && !historyError && (
                        <p className="history-empty">No conversions yet.</p>
                    )}
                    <div className="history-list">
                        {history
                            .filter((item) =>
                                (item.sourceCode ?? item.pythonCode ?? "")
                                    .toLowerCase()
                                    .includes(search.toLowerCase()),
                            )
                            .map((item, i) => {
                                const source = (
                                    item.sourceCode ??
                                    item.pythonCode ??
                                    ""
                                ).trim();
                                const first =
                                    source.split("\n")[0] ||
                                    "Untitled conversion";
                                const id = item._id ?? item.id ?? i;
                                return (
                                    <button
                                        className={`history-item ${activeId === id ? "selected" : ""}`}
                                        key={id}
                                        onClick={() => openHistory(item)}
                                        title={first}
                                    >
                                        <span className="history-code-icon">
                                            âŒ˜
                                        </span>
                                        <span className="history-item-body">
                                            <strong>
                                                {first.length > 30
                                                    ? first.slice(0, 30) + "â€¦"
                                                    : first}
                                            </strong>
                                            <small>
                                                {item.createdAt
                                                    ? new Date(
                                                          item.createdAt,
                                                      ).toLocaleString(
                                                          undefined,
                                                          {
                                                              month: "short",
                                                              day: "numeric",
                                                              hour: "numeric",
                                                              minute: "2-digit",
                                                          },
                                                      )
                                                    : "Saved conversion"}
                                            </small>
                                            <em>
                                                {item.method ||
                                                    "Python â†’ C++17"}
                                            </em>
                                        </span>
                                    </button>
                                );
                            })}
                    </div>
                </aside>
                <main className="main-content">
                    <div className="hero">
                        <div>
                            <h1>
                                Python <span>â†’ C++17</span>
                            </h1>
                            <p>Convert, validate and export clean C++ code.</p>
                        </div>
                    </div>

                    <div className="workspace-toolbar">
                        <div className="workspace-label">Code converter</div>
                        <div className="example-picker">
                            <label htmlFor="examples">Example</label>
                            <select
                                id="examples"
                                value={example}
                                onChange={(e) => {
                                    setExample(e.target.value);
                                    setSourceCode(examples[e.target.value]);
                                    resetResult();
                                }}
                            >
                                {Object.keys(examples).map((name) => (
                                    <option key={name}>{name}</option>
                                ))}
                            </select>
                        </div>
                    </div>

                    <div className="editors">
                        <Editor
                            title="Python source"
                            language="PYTHON"
                            code={sourceCode}
                            onChange={(value) => {
                                setSourceCode(value);
                                resetResult();
                            }}
                        />
                        <Editor
                            title="Generated C++"
                            language="C++17"
                            code={formatCppForDisplay(convertedCode)}
                        />
                    </div>


                    <section className="editor-panel">
                        <div className="panel-heading">
                            <strong>Custom Input (stdin)</strong>
                            <span className="language-tag">INPUT</span>
                        </div>
                        <div className="editor-area">
                            <textarea
                                aria-label="Custom Input"
                                placeholder="Example: 10 20 30 40"
                                value={stdin}
                                maxLength={4000}
                                onChange={(e) => {
                                    setStdin(e.target.value);
                                    resetResult();
                                }}
                                rows={4}
                            />
                        </div>
                    </section>

                    {ollamaCode && (
                        <div className="editors">
                            <Editor
                                title="Ollama AI Generated C++"
                                language="C++17"
                                code={formatCppForDisplay(ollamaCode)}
                            />
                        </div>
                    )}

                    {tripleResult && (
                        <section className="output-panel">
                            <div className="output-title">
                                Triple Validation: {tripleResult.validated
                                    ? "PASSED"
                                    : "FAILED"}
                            </div>
                            <p><strong>Python Output</strong></p>
                            <pre>{tripleResult.pythonOutput ?? ""}</pre>
                            <p><strong>AST C++ Output</strong></p>
                            <pre>{tripleResult.astOutput ?? ""}</pre>
                            <p><strong>Ollama C++ Output</strong></p>
                            <pre>{tripleResult.ollamaOutput ?? ""}</pre>
                        </section>
                    )}

                    <div className="actions">
                        <div className="primary-actions">
                            <button
                                className="btn btn-primary"
                                disabled={!!busy}
                                onClick={convert}
                            >
                                {busy === "convert"
                                    ? "Converting..."
                                    : "Convert to C++"}
                            </button>
                            <button
                                className="btn btn-outline"
                                disabled={!convertedCode || !!busy}
                                onClick={validate}
                            >
                                {busy === "validate"
                                    ? "Validating..."
                                    : "Validate C++"}
                            </button>
                        </div>
                        <div className="secondary-actions">
                            <button
                                className="btn btn-ghost"
                                disabled={!!busy}
                                onClick={() => {
                                    setSourceCode("");
                                    setStdin("");
                                    resetResult();
                                }}
                            >
                                Clear
                            </button>
                            <button
                                className="btn btn-ghost"
                                disabled={!convertedCode}
                                onClick={copy}
                            >
                                Copy
                            </button>
                            <button
                                className="btn btn-ghost"
                                disabled={!convertedCode}
                                onClick={download}
                            >
                                Download
                            </button>
                        </div>
                    </div>

                    {notice && (
                        <div role="status" className={`notice ${notice.type}`}>
                            {notice.text}
                        </div>
                    )}
                    {output !== "" && (
                        <section className="output-panel">
                            <div className="output-title">Execution output</div>
                            <pre>{output}</pre>
                        </section>
                    )}
                </main>
            </div>
        </div>
    );
}

