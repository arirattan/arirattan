# Updated tooltips with corrected content
import tkinter as tk

# ----------------------------
# TOOLTIP HELPER CLASS
# ----------------------------
class Tooltip:
    """Display a tooltip when hovering over a widget."""

    def __init__(self, widget: tk.Widget, text: str) -> None:
        self.widget = widget
        self.text = text
        self.tipwindow = None
        widget.bind("<Enter>", self.show)
        widget.bind("<Leave>", self.hide)

    def show(self, event: tk.Event | None = None) -> None:
        if self.tipwindow or not self.text:
            return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 2
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(
            tw,
            text=self.text,
            justify="left",
            background="#ffffe0",
            relief="solid",
            borderwidth=1,
            font=(None, 9),
            wraplength=400,
        )
        label.pack(ipadx=4, ipady=2)

    def hide(self, event: tk.Event | None = None) -> None:
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()

# ----------------------------
# SECTION TOOLTIPS DICTIONARY
# ----------------------------
SECTION_TOOLTIPS = {
    "secureme-language": "Localization settings for the Secure.me Web SDK (e.g. text, error messages, language translations).",
    "shared": "Shared configuration across multiple services (endpoints, timeouts, retention policies).",
    "secureme": "Secure.me Web SDK—controls session behavior, UI flow, network callbacks, and theming.",
    "mobilesdk": (
        "Mobile SDK settings—camera options, retry logic, liveness challenges, and SDC toggles.\n"
        "\nConfiguration & Flow Layout:\n"
        "Specify Passive Face Liveness retries, manual capture durations, and whether to record the screen.\n"
        "\nActive Face Liveness:\n"
        "Configure AFL options such as PFL max tries, AFL max tries, timeout, and mandatory flags.\n"
        "\nSmart Document Capture:\n"
        "Options to detect/display barcode, set SDC timeouts, and enable local/remote SDC.\n"
        "\nAu10Tix Web App Kit:\n"
        "Enable SDC front/back, PFL, POA, and adjust kit behaviors for full web integration."
    ),
    "bos": "Business Object Service (BOS)—backend verification orchestration, address matching, face comparison thresholds.",
    "outbox": "Outbox queue configuration—event payload mapping, webhook endpoints, retry/backoff settings.",
    "instinct": "Instinct fraud detection—historical data lookup, risk indicator thresholds, repetition checks.",
    "schematest": "Schema test parameters—used to validate JSON structure and run example test cases.",
    "mobiledemo": "Mobile demo configuration—sample flows for SDC, PFL, and POA with aggregated result display.",
    "edv": "Electronic Data Vault (EDV)—controls secure data storage, encryption keys, and retrieval policies.",
    "riskmanager": "Risk Manager settings—defines conflict thresholds, attack magnitude ranges, and logic connections.",
    "doublecheck": "Secondary review settings—timing rules, notification toggles, and available double-check services.",
    "bv": "Business Verification—fuzzy matching logic, ID length constraints, and provider-specific flows.",
    "checksscan": "Check/scan service—parameters for scanning documents and images, including type filters.",
    "console": "Console UI flags—toggles for upload restrictions, tolerance display, and session recording percentages.",
    "eds": "Electronic Document Service (EDS)—document handling rules, KYB settings, and provider integration.",
    "media": "Media processing—image/video token expiry, compression endpoints, and streaming rules.",
    "phone-email-verification": "OTP settings—PIN length, retry attempts, record lifetimes, and supported channels.",
    "sdc": (
        "Serial Fraud Monitor Settings—configure SDC in the General and Advanced Configuration tabs.\n\n"
        "General Configuration:\n"
        "• Enable saving hashed document data in SDC to store ID documents and images.\n"
        "• Enable Query SDC to add SDC analysis in the ID Verification flow (ignores Venture settings).\n"
        "• Query Data Sources: select Historical, Public Exposed Documents, or Consumer Source Risk Flag.\n"
        "• Enable Image Quality to allow analysis of poor-quality images.\n"
        "• Enable Biometrics to save facial identifiers in SDC database.\n"
        "• Enable Data Sharing Policy to share ID data with consortium organizations and allow querying later.\n"
        "• Ignore Countries List: add countries to exclude their data from SDC analysis.\n"
        "• API Result Detail Level: toggle Hide Conflict Info and Hide Repetition to control user-facing details.\n"
        "Remember to Save & Publish when finished.\n\n"
        "Advanced Configuration:\n"
        "(Next page details not provided)"
    ),
    "countriesAndIds": (
        "ID Verification Settings—use the Countries and IDs Settings tab to configure document handling policies per country.\n\n"
        "• Default Settings: ID Verification Block and Mandatory Both Sides unchecked.\n"
        "• Document column follows Supported Document List; single-side-only documents disable both-sides option.\n\n"
        "• Document Versions: modify one version per line, multiple versions via More Actions, or all versions by filtering 'All'.\n\n"
        "• Other Options: Checking ID Verification Block blocks document types from use; Mandatory Both Sides enforces collection of both sides; if a document lacks a backside, both-sides options are disabled.\n"
        "Remember to Save & Publish when finished."
    ),
    "piiRedaction": (
        "PII Redaction Settings—configure how Personally Identifiable Information is masked and retained.\n\n"
        "(Details to be added)"
    ),
    "eid": "Electronic ID (eID) settings—supported vendor endpoints, format versions, and autofill behavior.",
    "webapp": (
        "AU10TIX Web App Overview:\n"
        "In the AU10TIX Console, navigate to Settings > Products to access AU10TIX Web App settings. Ensure you are editing the correct organization by checking the organization name under your profile.\n"
        "The settings page is divided into four tabs: Visual Layout, Flow Layout, General Configuration, and Advanced Configuration.\n\n"
        "Visual Layout:\n"
        "• Company: Enter your company name, select or create a Venture, upload a logo and a loading animation (supported formats: GIF, SVG, PNG; recommended size: 430px x 700px).\n"
        "• Text Customization: Select or upload custom text templates, choose application font (default Montserrat).\n"
        "• Theme: Toggle light/dark background, set Primary, Success, and Failure colors for buttons and icons. Remember to Save & Publish or Discard Changes.\n"
        "• Animations: Select light/dark animation theme, upload Lottie JSON files for ID, Selfie, POA, Video Session, Voice Consent, Document Thickness, and ID2 animations.\n\n"
        "Flow Layout:\n"
        "• eID Flow: Enable IP-based eID country auto-complete.\n"
        "• Opening Screen & Wizard: Include or exclude an opening page and wizard steps bar; toggle Acceptable Documents list.\n"
        "• Platform: Enable PC or Mobile (QR scanning) flows; mobile flow prompts users to switch via QR code.\n"
        "• Legal Consent: Display a terms consent form (paste text or provide URL in Markdown).\n"
        "• ID Classification and Collection Policy: Choose Auto ID classification (with optional manual fallback), Manual ID classification (user declaration), or No ID classification. Configure default country and IP-based autofill.\n"
        "• Flow ID Verification Request Flow: Configure capture options (front/back, POA, Selfie, Voice Consent, Video Session) with Camera/Image upload or Both. Set recording times, language, user agreement toggles, and header for POA.\n"
        "• Document Thickness: Enable, set front/back/instructions durations, and require user approval if needed.\n\n"
        "General Configuration:\n"
        "• Default Invitation Text: Customize invitation message.\n"
        "• Token Expiration: Set token validity (minutes, hours, days).\n"
        "• Language: Choose application language, toggle language selector, or enable automatic browser-based language.\n"
        "• Other Features: Toggle Accessibility panel, Help button, Powered by AU10TIX logo, Front/Back Comparison, Enhanced SDC Feedback, POA Auto Capture, Screen Replay, Kiosk Mode (front-facing camera).\n\n"
        "Advanced Configuration:\n"
        "• Redirects: Configure success/failure redirect URLs and mobile callback behaviors (e.g., always use redirects, use after desktop-to-mobile, never use mobile redirects).\n"
        "• Image Type: Choose how to receive images (URL or Base64).\n"
        "• Request Headers: Add custom header key:value pairs for session result webhooks.\n"
        "Remember to Save & Publish or Discard Changes when finished."
    ),
    "workflow": "Workflow sequences—defines service order, retry logic, and expiration time for sessions.",
    "policy": "Policy manager—custom rule definitions, event-based triggers, and active policy toggles.",
    "biometrics": "Biometrics parameters—face match thresholds, liveness challenge settings, and injection protections.",
}
