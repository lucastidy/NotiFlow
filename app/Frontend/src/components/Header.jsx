import "./styles/Header.css";
import logo from "../assets/NotiFlow_Logo.png"

/**
 * Header Component
 *
 * Renders the top header section of the extension UI, including:
 *   - the NotiFlow logo
 *   - the NotiFlow title
 *
 * @returns {JSX.Element} The styled header bar with logo and title.
 */
export default function Header(){
    return (
        <>
            <div className="header-container">
                <div className ="header-title-container">
                    <img className="header-image" src={logo}></img>
                    <h1 className="header-title">NotiFlow</h1>
                </div>
            </div>
            <hr></hr>
        </>
    )
}
