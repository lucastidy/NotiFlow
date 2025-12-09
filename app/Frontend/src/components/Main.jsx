import { useState } from "react";
import "./styles/Main.css";
import ComponentSelect from "./ComponentSelect";

const COMPONENT_TABS = ["Classes", "Assignments", "Midterms", "Finals"];

/**
 * Main Component
 *
 * Serves as the top-level controller for the popup UI. Manages the
 * currently active tab and renders:
 *   - the tab selection buttons
 *   - the corresponding page content through ComponentSelect
 *
 * @returns {JSX.Element} The complete main layout with tab buttons and content.
 */
export default function Main() {
  const [activeTab, setActiveTab] = useState(COMPONENT_TABS[0]);

  return (
    <>
      <div className="main-container">
        <div className="main-components-container">
          {COMPONENT_TABS.map((tab) => (
            <button
              key={tab}
              className={`main-component ${activeTab === tab ? "active" : ""}`}
              onClick={() => setActiveTab(tab)}
            >
              {tab}
            </button>
          ))}
        </div>
      </div>
      <ComponentSelect selectedTab={activeTab} />
    </>
  );
}
