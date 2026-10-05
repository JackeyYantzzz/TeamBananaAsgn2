// Fill out your copyright notice in the Description page of Project Settings.

#include "MyPaperCharacter.h"
#include "PaperFlipbookComponent.h"
#include "Components/InputComponent.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Kismet/GameplayStatics.h"

AMyPaperCharacter::AMyPaperCharacter()
{
	PrimaryActorTick.bCanEverTick = true;
	JumpMaxCount = 1;

	// Initialize health
	MaxHealth = 3;
	CurrentHealth = 3;
}

void AMyPaperCharacter::Tick(float DeltaTime)
{
	Super::Tick(DeltaTime);

	// 1. Fall into the void (Death Check): If Z coordinate is below -600, restart the level
	if (GetActorLocation().Z < -600.0f)
	{
		// Restart the current level immediately upon falling
		UGameplayStatics::OpenLevel(GetWorld(), FName(*GetWorld()->GetName()));
		return; // Exit Tick to prevent further processing after death
	}

	// 2. Air / Jump state animation logic
	if (GetCharacterMovement()->IsFalling())
	{
		if (JumpAnimation && GetSprite()->GetFlipbook() != JumpAnimation)
		{
			GetSprite()->SetFlipbook(JumpAnimation);
		}
	}
	else
	{
		// 3. Ground state: check lateral speed for running vs standing still
		float LateralSpeed = GetVelocity().Size2D();

		if (LateralSpeed > 5.0f) // Moving
		{
			if (RunAnimation && GetSprite()->GetFlipbook() != RunAnimation)
			{
				GetSprite()->SetFlipbook(RunAnimation);
			}
		}
		else // Standing still (Idle)
		{
			if (IdleAnimation && GetSprite()->GetFlipbook() != IdleAnimation)
			{
				GetSprite()->SetFlipbook(IdleAnimation);
			}
		}
	}
}

void AMyPaperCharacter::SetupPlayerInputComponent(UInputComponent* PlayerInputComponent)
{
	Super::SetupPlayerInputComponent(PlayerInputComponent);

	PlayerInputComponent->BindAxis("MoveRight", this, &AMyPaperCharacter::MoveRight);
	PlayerInputComponent->BindAction("Jump", IE_Pressed, this, &AMyPaperCharacter::Jump);
	PlayerInputComponent->BindAction("Jump", IE_Released, this, &AMyPaperCharacter::StopJumping);
}

void AMyPaperCharacter::MoveRight(float Value)
{
	if (Controller != nullptr && Value != 0.0f)
	{
		AddMovementInput(FVector(1.0f, 0.0f, 0.0f), Value);

		if (Value > 0.0f)
		{
			GetSprite()->SetRelativeRotation(FRotator(0.0f, 0.0f, 0.0f));
		}
		else if (Value < 0.0f)
		{
			GetSprite()->SetRelativeRotation(FRotator(0.0f, 180.0f, 0.0f));
		}
	}
}

void AMyPaperCharacter::UnlockDoubleJump()
{
	JumpMaxCount = 2;
}

void AMyPaperCharacter::TakeDamageCustom(int32 DamageAmount)
{
	CurrentHealth -= DamageAmount;
	if (CurrentHealth < 0)
	{
		CurrentHealth = 0;
	}

	// Print debug message showing current health
	GEngine->AddOnScreenDebugMessage(-1, 3.0f, FColor::Red, FString::Printf(TEXT("Player Damaged! Current Health: %d / %d"), CurrentHealth, MaxHealth));

	// If health drops to 0, restart the level
	if (CurrentHealth <= 0)
	{
		GEngine->AddOnScreenDebugMessage(-1, 5.0f, FColor::Red, TEXT("Player Died! Restarting level..."));
		UGameplayStatics::OpenLevel(this, FName(*GetWorld()->GetName()));
	}
}