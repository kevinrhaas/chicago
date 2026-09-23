using UnrealBuildTool;
public class Chicago4DTarget : TargetRules { public Chicago4DTarget(TargetInfo Target) : base(Target) { Type = TargetType.Game; DefaultBuildSettings = BuildSettingsVersion.Latest; IncludeOrderVersion = EngineIncludeOrderVersion.Latest; ExtraModuleNames.Add("Chicago4D"); } }
