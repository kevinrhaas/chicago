using UnrealBuildTool;
public class Chicago4DEditorTarget : TargetRules { public Chicago4DEditorTarget(TargetInfo Target) : base(Target) { Type = TargetType.Editor; DefaultBuildSettings = BuildSettingsVersion.Latest; IncludeOrderVersion = EngineIncludeOrderVersion.Latest; ExtraModuleNames.Add("Chicago4D"); } }
