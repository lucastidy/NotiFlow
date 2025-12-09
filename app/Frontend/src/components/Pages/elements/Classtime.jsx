import "./styles/Classtime.css";
import { useState, useEffect } from "react";

export default function Classtime({ onSave, initialData }) {
  const [className, setClassName] = useState("");
  const [days, setDays] = useState({ M: false, Tu: false, W: false, Th: false, F: false });
  const [startTime, setStartTime] = useState("");
  const [endTime, setEndTime] = useState("");

  useEffect(() => {
    if (initialData) {
      setClassName(initialData.className);
      setDays(initialData.days);
      setStartTime(initialData.startTime);
      setEndTime(initialData.endTime);
    }
  }, [initialData]);

  function generateTimes() {
    const times = [];
    let hour = 8;
    let minute = 0;

    while (hour < 21 || (hour === 21 && minute === 0)) {
      const suffix = hour >= 12 ? "PM" : "AM";
      const displayHour = hour > 12 ? hour - 12 : hour;
      const displayMinute = minute === 0 ? "00" : minute;
      times.push(`${displayHour}:${displayMinute} ${suffix}`);

      minute += 30;
      if (minute === 60) {
        minute = 0;
        hour++;
      }
    }
    return times;
  }

  const allTimes = generateTimes();

  function timeToMinutes(t) {
    if (!t) return null;
    const [time, suffix] = t.split(" ");
    let [h, m] = time.split(":").map(Number);
    if (suffix === "PM" && h !== 12) h += 12;
    if (suffix === "AM" && h === 12) h = 0;
    return h * 60 + m;
  }

  const validEndTimes = startTime
    ? allTimes.filter(t => timeToMinutes(t) >= timeToMinutes(startTime) + 30)
    : allTimes;

  const isValid =
    className.trim() !== "" &&
    Object.values(days).some(d => d) &&
    startTime !== "" &&
    endTime !== "";

  function handleSubmit() {
    if (!isValid) return;
    onSave({ className, days, startTime, endTime });
    setClassName("");
    setDays({ M: false, Tu: false, W: false, Th: false, F: false });
    setStartTime("");
    setEndTime("");
    
  }

  return (
    <div className="class-input-block">
      <h3>Add Class:</h3>

    <div className="class-name-row">
        <span>Course:</span>
        <input
            className="course-input"
            value={className}
            onChange={e => setClassName(e.target.value)}
        />
    </div>


      <div className="day-checkboxes">
        {Object.keys(days).map(d => (
          <label key={d} className="day-label">
            <input
              type="checkbox"
              checked={days[d]}
              onChange={() => setDays(prev => ({ ...prev, [d]: !prev[d] }))}
            />
            {d}
          </label>
        ))}
      </div>

      <div className="time-row">
        <div className="time-select">
          <span>Start:</span>
          <select
            value={startTime}
            onChange={e => {
              setStartTime(e.target.value);
              setEndTime("");
            }}
          >
            <option value="">--</option>
            {allTimes.map(t => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>
        </div>    
        <div className="time-select">
          <span>End:</span>
          <select
            value={endTime}
            onChange={e => setEndTime(e.target.value)}
            disabled={!startTime}
            className={!startTime ? "time-disabled" : ""}
          >

            <option value="">--</option>
            {validEndTimes.map(t => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>
        </div>
      </div>
    <div className="classtime-button-container">
      <button
        className="add-btn"
        disabled={!isValid}
        onClick={handleSubmit}
      >
        {initialData ? "Save Changes" : "Add Class"}
      </button>
    </div>
    </div>
  );
}

