#define MyAppName "Pokemon Inventory & Deck Builder"
#define MyAppVersion "1.0.0"
#define MyAppExeName "Pokemon Inventory Deck Builder.exe"

[Setup]
AppId={{B7240D7C-9C5E-4D16-AD72-3954C67C1A54}
AppName={#MyAppName}
AppVersion={#MyAppVersion}

DefaultDirName={localappdata}\Programs\Pokemon Inventory Deck Builder
DefaultGroupName={#MyAppName}

PrivilegesRequired=lowest

OutputDir=installer_output
OutputBaseFilename=Pokemon Inventory Deck Builder Setup 1.0.0

SetupIconFile=assets\app_icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}

Compression=lzma2
SolidCompression=yes
WizardStyle=modern

ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

CloseApplications=yes

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked

[Files]
Source: "dist\Pokemon Inventory Deck Builder\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent