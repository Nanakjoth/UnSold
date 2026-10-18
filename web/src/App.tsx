import { BrowserRouter, Route, Routes } from "react-router-dom";
import DemoBanner from "./components/DemoBanner";
import { SessionProvider } from "./hooks/useSession";
import Advice from "./pages/Advice";
import Sessions from "./pages/Sessions";
import Explore from "./pages/Explore";
import InterestDetailPage from "./pages/InterestDetail";
import Saved from "./pages/Saved";
import Profile from "./pages/Profile";
import InProgress from "./pages/InProgress";
import Metrics from "./pages/Metrics";
import Trust from "./pages/Trust";
import { About, Privacy, Terms } from "./pages/Static";

export default function App() {
  return (
    <SessionProvider>
      <BrowserRouter>
        <div className="flex min-h-screen flex-col">
          <DemoBanner />
          <main className="flex-1">
            <Routes>
              {/* Advice is the core product and the front door. */}
              <Route path="/" element={<Advice />} />
              <Route path="/advice" element={<Advice />} />
              {/* Sessions + Guardian (Stage A2). */}
              <Route path="/sessions" element={<Sessions />} />
              <Route path="/sessions/:id" element={<Sessions />} />
              {/* Discovery is the supporting add-on. */}
              <Route path="/explore" element={<Explore />} />
              <Route path="/interests/:slug" element={<InterestDetailPage />} />
              <Route path="/saved" element={<Saved />} />
              {/* Guardian agreement metrics (Stage A3). */}
              <Route path="/metrics" element={<Metrics />} />
              {/* Full transparency surface (UI redesign spec section 7). */}
              <Route path="/trust" element={<Trust />} />
              <Route path="/profile" element={<Profile />} />
              <Route path="/about" element={<About />} />
              <Route path="/privacy" element={<Privacy />} />
              <Route path="/terms" element={<Terms />} />
              <Route
                path="*"
                element={
                  <InProgress
                    title="Page not found"
                    detail="That page does not exist yet."
                  />
                }
              />
            </Routes>
          </main>
        </div>
      </BrowserRouter>
    </SessionProvider>
  );
}
