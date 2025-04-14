; File: qa_verifier_installer.iss
[Setup]
AppName=QA Verifier Professional Edition
AppVersion=4.21
AppPublisher=Your Company Name
AppPublisherURL=https://example.com
DefaultDirName={autopf}\QA Verifier Pro
DefaultGroupName=QA Verifier Pro
UninstallDisplayIcon={app}\QA Verifier Pro.exe
Compression=lzma2
SolidCompression=yes
OutputDir=installer
OutputBaseFilename=QA_Verifier_Pro_Setup
SetupIconFile=resources\fileconverter.ico
WizardStyle=modern
PrivilegesRequired=lowest
; Change to 'admin' only if absolutely necessary
;PrivilegesRequired=admin
DiskSpanning=yes

[Files]
Source: "dist\QA Verifier Pro\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Dirs]
; Ensure user data directory exists with proper permissions
Name: "{localappdata}\QA_Verifier"; Permissions: users-full

[Icons]
Name: "{group}\QA Verifier Pro"; Filename: "{app}\QA Verifier Pro.exe"
Name: "{commondesktop}\QA Verifier Pro"; Filename: "{app}\QA Verifier Pro.exe"
Name: "{group}\Uninstall QA Verifier Pro"; Filename: "{uninstallexe}"

[Run]
Filename: "{app}\QA Verifier Pro.exe"; Description: "Launch QA Verifier Pro"; Flags: nowait postinstall skipifsilent