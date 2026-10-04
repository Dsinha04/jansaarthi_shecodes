import { AppProvider, useApp } from "./store";
import ComplaintScreen from "./screens/ComplaintScreen";
import HomeScreen from "./screens/HomeScreen";
import LanguageScreen from "./screens/LanguageScreen";
import LoginScreen from "./screens/LoginScreen";
import RegisterScreen from "./screens/RegisterScreen";
import ReceiptScreen from "./screens/ReceiptScreen";
import ResultScreen from "./screens/ResultScreen";
import ScanScreen from "./screens/ScanScreen";
import SchemesScreen from "./screens/SchemesScreen";
import VoiceScreen from "./screens/VoiceScreen";

function Router() {
  const { screen, session } = useApp();
  if (!session && !["language", "login", "register"].includes(screen.name)) return <LanguageScreen />;
  switch (screen.name) {
    case "language": return <LanguageScreen />;
    case "login": return <LoginScreen />;
    case "register": return <RegisterScreen />;
    case "home": return <HomeScreen />;
    case "voice": return <VoiceScreen />;
    case "scan": return <ScanScreen />;
    case "schemes": return <SchemesScreen />;
    case "complaint": return <ComplaintScreen />;
    case "result": return <ResultScreen view={screen.view} />;
    case "receipt": return <ReceiptScreen req={screen.req} />;
  }
}
export default function App() { return <AppProvider><Router /></AppProvider>; }