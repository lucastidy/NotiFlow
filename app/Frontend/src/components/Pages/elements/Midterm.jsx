import "./styles/Midterm.css"

/**
 * Midterm Component
 *
 * Renders a styled card displaying midterm exam information for a course.
 * Shows:
 *   - course name
 *   - midterm date
 *   - midterm time
 *   - exam location
 *
 * @returns {JSX.Element} A card UI block showing midterm exam details.
 */
export default function Midterm(props){
    const { className, date, begin_date_time, end_date_time, location } = props;

    return (
        <div className="midterm-card">
            <div className="midterm-container">
                <div className="midterm-name">{className}</div>
                <div className="midterm-detail">
                    <strong>Date:</strong> {date}
                </div>
                <div className="midterm-detail">
                    <strong>Start Time:</strong> {begin_date_time}
                </div>
                <div className="midterm-detail">
                    <strong>End Time:</strong> {end_date_time}
                </div>
                <div className="midterm-detail">
                    <strong>Location:</strong> {location}
                </div>
            </div>
            <hr className="midterm-line"></hr>
        </div>
    )
}
