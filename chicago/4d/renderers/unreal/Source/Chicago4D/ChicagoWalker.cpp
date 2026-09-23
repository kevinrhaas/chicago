#include "ChicagoWalker.h"
#include "Camera/CameraComponent.h"
#include "Components/CapsuleComponent.h"
#include "Components/InputComponent.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/PlayerController.h"
#include "Kismet/GameplayStatics.h"
#include "Kismet/KismetSystemLibrary.h"
#include "Engine/Canvas.h"
#include "Engine/Engine.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
AChicagoWalker::AChicagoWalker() {
 PrimaryActorTick.bCanEverTick = true;
 GetCapsuleComponent()->InitCapsuleSize(34.f, 96.f);
 UCameraComponent* Camera=CreateDefaultSubobject<UCameraComponent>(TEXT("Eyes"));
 Camera->SetupAttachment(GetCapsuleComponent()); Camera->SetRelativeLocation(FVector(0,0,64)); Camera->bUsePawnControlRotation=true;
 GetCharacterMovement()->MaxWalkSpeed=300.f; GetCharacterMovement()->JumpZVelocity=420.f;
 GetCharacterMovement()->MaxStepHeight=40.f;
 bUseControllerRotationYaw=true;
}
void AChicagoWalker::BeginPlay() {
 Super::BeginPlay();
 bWalkTest = FParse::Param(FCommandLine::Get(), TEXT("ChicagoWalkTest"));
 TestStart = GetActorLocation();
 if(APlayerController* PC=Cast<APlayerController>(GetController())) { PC->SetInputMode(FInputModeGameOnly()); PC->bShowMouseCursor=false; }
}
void AChicagoWalker::Tick(float DeltaSeconds) {
 Super::Tick(DeltaSeconds);
 // An opt-in packaged integration check uses the same movement path as WASD.
 // It never teleports, changes movement mode, or disables collision.
 if (!bWalkTest) return;
 if (Controller) Controller->SetControlRotation(FRotator(0.f, 90.f, 0.f));
 TestSeconds += DeltaSeconds;
 if (TestSeconds >= 2.f && TestSeconds < 16.f) Forward(1.f);
 if (TestSeconds >= 16.f && TestSeconds < 20.f) Forward(-1.f);
 const int32 Second = FMath::FloorToInt(TestSeconds);
 if (Second != LastTestSecond) {
  LastTestSecond = Second;
  UE_LOG(LogTemp, Display, TEXT("CHICAGO_WALK_TEST second=%d location=%s speed=%.2f walking=%d"),
   Second, *GetActorLocation().ToString(), GetVelocity().Size(), GetCharacterMovement()->IsMovingOnGround());
 }
 if (TestSeconds >= 21.f) {
  const bool bPassed = GetCharacterMovement()->IsMovingOnGround()
   && FVector::Dist2D(TestStart, GetActorLocation()) > 100.f
   && FMath::Abs(GetActorLocation().Z - TestStart.Z) < 300.f;
  UE_LOG(LogTemp, Display, TEXT("CHICAGO_WALK_TEST_RESULT %s"), bPassed ? TEXT("PASS") : TEXT("FAIL"));
  Quit();
 }
}
void AChicagoWalker::SetupPlayerInputComponent(UInputComponent* Input) {
 Super::SetupPlayerInputComponent(Input);
 // A background integration run must not consume the owner's keyboard/mouse.
 if (FParse::Param(FCommandLine::Get(), TEXT("ChicagoWalkTest"))) return;
 Input->BindAxis("Forward",this,&AChicagoWalker::Forward); Input->BindAxis("Right",this,&AChicagoWalker::Right);
 Input->BindAxis("LookX",this,&AChicagoWalker::LookX); Input->BindAxis("LookY",this,&AChicagoWalker::LookY);
 Input->BindAction("Jump",IE_Pressed,this,&ACharacter::Jump); Input->BindAction("Jump",IE_Released,this,&ACharacter::StopJumping);
 Input->BindAction("Quit",IE_Pressed,this,&AChicagoWalker::Quit); Input->BindAction("Reset",IE_Pressed,this,&AChicagoWalker::ResetWalk);
}
void AChicagoWalker::Forward(float V) { AddMovementInput(FRotationMatrix(FRotator(0,GetControlRotation().Yaw,0)).GetUnitAxis(EAxis::X),V); }
void AChicagoWalker::Right(float V) { AddMovementInput(FRotationMatrix(FRotator(0,GetControlRotation().Yaw,0)).GetUnitAxis(EAxis::Y),V); }
void AChicagoWalker::LookX(float V) { AddControllerYawInput(V); }
void AChicagoWalker::LookY(float V) { AddControllerPitchInput(V); }
void AChicagoWalker::Quit() { UKismetSystemLibrary::QuitGame(this,Cast<APlayerController>(GetController()),EQuitPreference::Quit,false); }
void AChicagoWalker::ResetWalk() { UGameplayStatics::OpenLevel(this,FName(*UGameplayStatics::GetCurrentLevelName(this))); }
void AChicagoHUD::DrawHUD() {
 Super::DrawHUD(); if(!Canvas) return;
 DrawRect(FLinearColor(0,0,0,0.65f),12,12,590,62);
 DrawText(TEXT("CHICAGO 1835 | Development preview"),FLinearColor::White,24,20,GEngine->GetSmallFont(),1.2f);
 DrawText(TEXT("WASD: walk   Mouse: look   Space: jump   R: restart   Esc: quit"),FLinearColor::White,24,47,GEngine->GetSmallFont());
}
AChicagoGameMode::AChicagoGameMode() { DefaultPawnClass=AChicagoWalker::StaticClass(); HUDClass=AChicagoHUD::StaticClass(); }
