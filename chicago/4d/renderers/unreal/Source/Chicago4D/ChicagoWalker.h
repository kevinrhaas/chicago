#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "GameFramework/GameModeBase.h"
#include "GameFramework/HUD.h"
#include "ChicagoWalker.generated.h"
UCLASS()
class CHICAGO4D_API AChicagoWalker : public ACharacter {
 GENERATED_BODY()
public:
 AChicagoWalker();
 virtual void SetupPlayerInputComponent(UInputComponent* Input) override;
 virtual void BeginPlay() override;
 virtual void Tick(float DeltaSeconds) override;
private:
 void Forward(float Value); void Right(float Value); void LookX(float Value); void LookY(float Value);
 void Quit(); void ResetWalk();
 bool bWalkTest = false;
 float TestSeconds = 0.f;
 int32 LastTestSecond = -1;
 FVector TestStart = FVector::ZeroVector;
};
UCLASS()
class CHICAGO4D_API AChicagoHUD : public AHUD {
 GENERATED_BODY()
public: virtual void DrawHUD() override;
};
UCLASS()
class CHICAGO4D_API AChicagoGameMode : public AGameModeBase {
 GENERATED_BODY()
public: AChicagoGameMode();
};
