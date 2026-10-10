; Inno Setup script for the Windows installer (built in CI: .github/workflows/release.yml)
#define AppVersion GetEnv("APP_VERSION")

[Setup]
AppName=Power Equipment Studio
AppVersion={#AppVersion}
AppPublisher=Power Equipment Engineering contributors
AppPublisherURL=https://github.com/prriyamm/power-equipment-engineering
DefaultDirName={autopf}\Power Equipment Studio
DefaultGroupName=Power Equipment Studio
OutputDir=..\dist
OutputBaseFilename=PowerEquipmentStudio-{#AppVersion}-windows-setup
Compression=lzma2
SolidCompression=yes
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
LicenseFile=..\LICENSE
UninstallDisplayIcon={app}\PowerEquipmentStudio.exe
WizardStyle=modern

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Shortcuts:"

[Files]
Source: "..\dist\PowerEquipmentStudio\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion

[Icons]
Name: "{group}\Power Equipment Studio"; Filename: "{app}\PowerEquipmentStudio.exe"
Name: "{group}\Uninstall Power Equipment Studio"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Power Equipment Studio"; Filename: "{app}\PowerEquipmentStudio.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\PowerEquipmentStudio.exe"; Description: "Launch Power Equipment Studio"; Flags: nowait postinstall skipifsilent
