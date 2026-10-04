import type { Lang } from "./types";

export const LANGUAGES: { code: Lang; native: string; english: string }[] = [
  { code: "hi", native: "हिन्दी", english: "Hindi" },
  { code: "en", native: "English", english: "English" },
  { code: "bn", native: "বাংলা", english: "Bengali" },
  { code: "mr", native: "मराठी", english: "Marathi" },
  { code: "ta", native: "தமிழ்", english: "Tamil" },
  { code: "te", native: "తెలుగు", english: "Telugu" },
  { code: "gu", native: "ગુજરાતી", english: "Gujarati" },
  { code: "pa", native: "ਪੰਜਾਬੀ", english: "Punjabi" },
];

// Interface text exists for English and Hindi. Other languages show English interface text, while
// ANSWERS from the AI are still translated by the backend into the chosen language.
const en = {
  appName: "Jansaarthi", chooseLanguage: "Choose your language", login: "Log in", loginHint: "Tap your card or use your fingerprint",
  tapCard: "Tap your RFID card on the reader", orTypeCard: "Or type the card number", submit: "Submit",
  fingerprint: "Use fingerprint", fingerprintHint: "Place your finger on the sensor", guest: "Continue without login",
  welcome: "Welcome", home: "Home", back: "Back", logout: "Log out", cancel: "Cancel", next: "Next", yes: "Yes", no: "No", skip: "Don't know",
  askByVoice: "Ask by voice", scanDocument: "Scan a document", findSchemes: "Find schemes", makeComplaint: "Make a complaint",
  tapToSpeak: "Tap and speak your question", recording: "Listening… tap to stop", typeInstead: "Or type your question here",
  askNow: "Get answer", thinking: "Finding the answer…", transcribing: "Understanding your voice…", scanning: "Reading your document…",
  scanHint: "Take a clear photo of the paper or choose a file", takePhoto: "Take a photo", textFound: "Text found. Check and correct it.",
  analyzeContract: "Check contract for risks", checkNotice: "Check if message is fake", noText: "No text could be read. Try a clearer photo.",
  schemeQ1: "Does your family own farm land?", schemeQ2: "What work do you do? (choose all)", schemeQ3: "Are you a member of a cooperative society?",
  step: "Step", of: "of", showSchemes: "Show schemes",
  category: "What is your problem?", details: "Tell us what happened", detailsHint: "Write or speak in your own language", createComplaint: "Create complaint",
  result: "Result", answer: "Answer", sources: "Official sources", printReceipt: "Print", preview: "Print preview", printNow: "Print now",
  printed: "Printed. Please collect your paper.", notPrinted: "Printer is not available. Your copy is saved.", reference: "Reference number",
  steps: "What to do", askAnother: "Ask another", unverified: "This answer could not be checked against official papers. Do not rely on it.",
  offlineMode: "AI explanation is offline. Showing official passages only.", noEvidence: "No official information found. Please ask the society office.",
  riskLevel: "Risk level", noRisks: "No risky clauses found.", verdict: "Verdict", likelyFraud: "Likely fraud. Do not respond.", suspicious: "Suspicious. Be careful.",
  lowConcern: "Low concern.", noFlags: "No warning signs found.", eligible: "Likely eligible", checkDetails: "Check details", documentsNeeded: "Documents needed",
  whereApply: "Where to apply", notVerified: "Not yet verified by the team", translationWarn: "Translation was not available. Showing English.",
  readAloud: "Read aloud", stopReading: "Stop", bigText: "Bigger text", contrast: "High contrast", stillThere: "Are you still there?", tapToContinue: "Tap to continue",
  loading: "Please wait…", tryAgain: "Try again", members: "Society", name: "Name", memberNo: "Member no.",
  "cat.loan_dispute": "Loan problem", "cat.wrong_charges": "Wrong charges", "cat.membership_shares": "Membership / shares",
  "cat.management_election": "Management / election", "cat.fraud_misappropriation": "Fraud / missing money", "cat.other": "Something else",
  "occ.farmer": "Farmer", "occ.tenant_farmer": "Tenant farmer", "occ.sharecropper": "Sharecropper", "occ.dairy": "Dairy", "occ.fisher": "Fisher",
  "occ.poultry": "Poultry", "occ.shg_member": "Self-help group", "occ.artisan": "Artisan", "occ.other": "Other",
  "err.network": "Cannot reach the machine's server. Please ask for help.", "err.card_not_registered": "This card is not registered. Ask the society office.",
  "err.fingerprint_not_registered": "Fingerprint not recognised. Try again.", "err.ai_unavailable": "The AI service is not available right now.",
  "err.knowledge_base_missing": "The knowledge base is not ready.", "err.session_expired": "Your session ended. Please log in again.",
  "err.microphone": "Microphone is not available. Please type instead.", "err.camera": "Could not read the file.", "err.generic": "Something went wrong. Please try again.",
  profile: "My profile", notAssigned: "Not assigned", phone: "Phone number", address: "Address", profession: "Profession",
  landOwned: "Do you own land?", landArea: "Land area", register: "Register", registerNewUser: "New member? Register here",
  registrationApprovalHint: "New registrations are approved by the society office before you can log in.",
  registerHint: "Fill in your details. The society office will approve your registration.",
  registrationSubmitted: "Registration submitted", registrationPending: "Your registration is waiting for approval by the society office.", backToLogin: "Back to login",
  supportedDocuments: "Supported: photo, PDF or Word file", otherOccupation: "Other occupation", otherOccupationHint: "Type your work if it is not listed",
  schemeStep2Required: "Choose at least one option or type your work.",
  updateProfile: "Update profile", updatePendingBanner: "Your profile update is waiting for approval by the society office.",
  updateRejected: "Your last profile update was not approved", updateApproved: "Your last profile update was approved.",
  updateHint: "Change only what is wrong. Changes are applied after the society office approves them.",
  submitForApproval: "Send for approval", updateSubmitted: "Update sent", updateSubmittedText: "The society office will review your changes. Your profile stays the same until they approve.",
  currentlyPending: "You already have an update waiting for approval. You can send another after it is reviewed.",
  "err.update_already_pending": "You already have an update waiting for approval.", "err.no_changes": "You have not changed anything.",
  "err.profile_requires_login": "Please log in with your card to update your profile.",
  chooseFile: "Choose a file from this device",
};
export type Key = keyof typeof en;

const hi: Partial<Record<Key, string>> = {
  appName: "जनसारथी", chooseLanguage: "अपनी भाषा चुनें", login: "लॉग इन करें", loginHint: "अपना कार्ड लगाएँ या उँगली रखें",
  tapCard: "कार्ड को रीडर पर रखें", orTypeCard: "या कार्ड नंबर लिखें", submit: "आगे बढ़ें", fingerprint: "फिंगरप्रिंट से", fingerprintHint: "सेंसर पर उँगली रखें",
  guest: "बिना लॉग इन के आगे बढ़ें", welcome: "स्वागत है", home: "होम", back: "पीछे", logout: "लॉग आउट", cancel: "रद्द करें", next: "आगे", yes: "हाँ", no: "नहीं", skip: "पता नहीं",
  askByVoice: "बोलकर पूछें", scanDocument: "दस्तावेज़ स्कैन करें", findSchemes: "योजनाएँ खोजें", makeComplaint: "शिकायत दर्ज करें",
  tapToSpeak: "दबाएँ और अपना सवाल बोलें", recording: "सुन रहा हूँ… रोकने के लिए दबाएँ", typeInstead: "या अपना सवाल यहाँ लिखें",
  askNow: "जवाब पाएँ", thinking: "जवाब खोज रहे हैं…", transcribing: "आपकी आवाज़ समझ रहे हैं…", scanning: "दस्तावेज़ पढ़ रहे हैं…",
  scanHint: "कागज़ की साफ़ फ़ोटो लें या फ़ाइल चुनें", takePhoto: "फ़ोटो लें", textFound: "लिखा हुआ मिल गया। जाँचें और सुधारें।",
  analyzeContract: "अनुबंध में जोखिम जाँचें", checkNotice: "जाँचें कि संदेश नकली तो नहीं", noText: "कुछ पढ़ा नहीं जा सका। साफ़ फ़ोटो लें।",
  schemeQ1: "क्या आपके परिवार के पास खेती की ज़मीन है?", schemeQ2: "आप क्या काम करते हैं? (सभी चुनें)", schemeQ3: "क्या आप सहकारी समिति के सदस्य हैं?",
  step: "चरण", of: "/", showSchemes: "योजनाएँ दिखाएँ", category: "आपकी समस्या क्या है?", details: "क्या हुआ, बताएँ", detailsHint: "अपनी भाषा में लिखें या बोलें",
  createComplaint: "शिकायत बनाएँ", result: "नतीजा", answer: "जवाब", sources: "सरकारी स्रोत", printReceipt: "प्रिंट", preview: "प्रिंट देखें", printNow: "अभी प्रिंट करें",
  printed: "प्रिंट हो गया। कृपया कागज़ ले लें।", notPrinted: "प्रिंटर उपलब्ध नहीं है। आपकी प्रति सहेज ली गई है।", reference: "संदर्भ संख्या", steps: "क्या करें",
  askAnother: "दूसरा सवाल पूछें", unverified: "इस जवाब को सरकारी कागज़ों से मिलाया नहीं जा सका। इस पर भरोसा न करें।",
  offlineMode: "AI स्पष्टीकरण अभी बंद है। केवल सरकारी अंश दिखा रहे हैं।", noEvidence: "कोई सरकारी जानकारी नहीं मिली। कृपया समिति कार्यालय से पूछें।",
  riskLevel: "जोखिम स्तर", noRisks: "कोई जोखिम वाली शर्त नहीं मिली।", verdict: "नतीजा", likelyFraud: "धोखाधड़ी की आशंका। जवाब न दें।", suspicious: "संदिग्ध। सावधान रहें।",
  lowConcern: "कम चिंता।", noFlags: "कोई चेतावनी संकेत नहीं मिला।", eligible: "पात्र होने की संभावना", checkDetails: "विवरण जाँचें", documentsNeeded: "ज़रूरी दस्तावेज़",
  whereApply: "आवेदन कहाँ करें", notVerified: "टीम ने अभी जाँचा नहीं है", translationWarn: "अनुवाद उपलब्ध नहीं था। अंग्रेज़ी दिखा रहे हैं।", readAloud: "पढ़कर सुनाएँ",
  stopReading: "रोकें", bigText: "बड़े अक्षर", contrast: "ज़्यादा कंट्रास्ट", stillThere: "क्या आप अभी भी यहाँ हैं?", tapToContinue: "जारी रखने के लिए दबाएँ",
  loading: "कृपया प्रतीक्षा करें…", tryAgain: "फिर कोशिश करें", members: "समिति", name: "नाम", memberNo: "सदस्य संख्या",
  "cat.loan_dispute": "कर्ज़ की समस्या", "cat.wrong_charges": "गलत कटौती", "cat.membership_shares": "सदस्यता / शेयर", "cat.management_election": "प्रबंधन / चुनाव",
  "cat.fraud_misappropriation": "धोखाधड़ी / पैसे गायब", "cat.other": "कुछ और", "occ.farmer": "किसान", "occ.tenant_farmer": "बटाईदार किसान", "occ.sharecropper": "साझा खेती",
  "occ.dairy": "डेयरी", "occ.fisher": "मछुआरा", "occ.poultry": "मुर्गी पालन", "occ.shg_member": "स्वयं सहायता समूह", "occ.artisan": "कारीगर", "occ.other": "अन्य",
  "err.network": "मशीन का सर्वर नहीं मिल रहा। कृपया मदद माँगें।", "err.card_not_registered": "यह कार्ड पंजीकृत नहीं है। समिति कार्यालय से पूछें।",
  "err.fingerprint_not_registered": "फिंगरप्रिंट पहचाना नहीं गया। फिर कोशिश करें।", "err.ai_unavailable": "AI सेवा अभी उपलब्ध नहीं है।",
  "err.knowledge_base_missing": "जानकारी का भंडार तैयार नहीं है।", "err.session_expired": "आपका सत्र खत्म हो गया। फिर लॉग इन करें।",
  "err.microphone": "माइक्रोफ़ोन उपलब्ध नहीं। कृपया लिखकर पूछें।", "err.camera": "फ़ाइल पढ़ी नहीं जा सकी।", "err.generic": "कुछ गड़बड़ हुई। कृपया फिर कोशिश करें।",
  profile: "मेरी प्रोफ़ाइल", notAssigned: "नहीं दिया गया", phone: "फ़ोन नंबर", address: "पता", profession: "पेशा",
  landOwned: "क्या आपके पास ज़मीन है?", landArea: "ज़मीन का क्षेत्रफल", register: "पंजीकरण करें", registerNewUser: "नए सदस्य? यहाँ पंजीकरण करें",
  registrationApprovalHint: "लॉग इन से पहले समिति कार्यालय नए पंजीकरण को मंज़ूरी देता है।",
  registerHint: "अपना विवरण भरें। समिति कार्यालय आपके पंजीकरण को मंज़ूरी देगा।",
  registrationSubmitted: "पंजीकरण जमा हो गया", registrationPending: "आपका पंजीकरण समिति कार्यालय की मंज़ूरी की प्रतीक्षा में है।", backToLogin: "लॉग इन पर वापस जाएँ",
  supportedDocuments: "फ़ोटो, PDF या Word फ़ाइल चलेगी", otherOccupation: "अन्य काम", otherOccupationHint: "अगर सूची में नहीं है तो अपना काम लिखें",
  schemeStep2Required: "कम से कम एक विकल्प चुनें या अपना काम लिखें।",
  updateProfile: "प्रोफ़ाइल अपडेट करें", updatePendingBanner: "आपका प्रोफ़ाइल बदलाव समिति कार्यालय की मंज़ूरी की प्रतीक्षा में है।",
  updateRejected: "आपका पिछला प्रोफ़ाइल बदलाव मंज़ूर नहीं हुआ", updateApproved: "आपका पिछला प्रोफ़ाइल बदलाव मंज़ूर हो गया।",
  updateHint: "सिर्फ़ वही बदलें जो गलत है। बदलाव समिति कार्यालय की मंज़ूरी के बाद लागू होंगे।",
  submitForApproval: "मंज़ूरी के लिए भेजें", updateSubmitted: "बदलाव भेज दिया गया", updateSubmittedText: "समिति कार्यालय आपके बदलाव देखेगा। मंज़ूरी तक आपकी प्रोफ़ाइल वैसी ही रहेगी।",
  currentlyPending: "आपका एक बदलाव पहले से मंज़ूरी की प्रतीक्षा में है। जाँच के बाद आप दूसरा भेज सकते हैं।",
  "err.update_already_pending": "आपका एक बदलाव पहले से मंज़ूरी की प्रतीक्षा में है।", "err.no_changes": "आपने कुछ बदला नहीं है।",
  "err.profile_requires_login": "प्रोफ़ाइल अपडेट करने के लिए कार्ड से लॉग इन करें।",
  chooseFile: "इस डिवाइस से फ़ाइल चुनें",
};

const TABLES: Partial<Record<Lang, Partial<Record<Key, string>>>> = { hi };

export function translator(lang: Lang) {
  const table = TABLES[lang];
  return (key: Key): string => table?.[key] ?? en[key];
}

/** Look up any string key (used for server error codes). Returns undefined if there is no text for it. */
export function lookup(lang: Lang, key: string): string | undefined {
  return (TABLES[lang] as Record<string, string> | undefined)?.[key] ?? (en as Record<string, string>)[key];
}

/** Speech synthesis locale for each language. */
export const TTS_LOCALE: Record<Lang, string> = { en: "en-IN", hi: "hi-IN", bn: "bn-IN", mr: "mr-IN", ta: "ta-IN", te: "te-IN", gu: "gu-IN", pa: "pa-IN" };