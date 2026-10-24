import { BrowserRouter, Routes, Route } from "react-router-dom";
import InvestigationPage from "./pages/InvestigationPage.jsx";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<InvestigationPage />} />
      </Routes>
    </BrowserRouter>
  );
}
