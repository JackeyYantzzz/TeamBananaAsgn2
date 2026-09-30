// Fill out your copyright notice in the Description page of Project Settings.

#include "MyPaperCharacter.h"
#include "PaperFlipbookComponent.h"
#include "Components/InputComponent.h"
#include "GameFramework/CharacterMovementComponent.h"

AMyPaperCharacter::AMyPaperCharacter()
{
	// Enable Tick per frame
	PrimaryActorTick.bCanEverTick = true;

	// Set default max jump count to 1 (single jump)
	JumpMaxCount = 1;
}

void AMyPaperCharacter::Tick(float DeltaTime)
{
	Super::Tick(DeltaTime);

	// 1. If the character is in the air (jumping or falling)
	if (GetCharacterMovement()->IsFalling())
	{
		if (JumpAnimation && GetSprite()->GetFlipbook() != JumpAnimation)
		{
			GetSprite()->SetFlipbook(JumpAnimation);
		}
	}
	else
	{
		// 2. If on the ground: check lateral speed to distinguish running vs standing still
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

	// 1. Bind the "MoveRight" axis mapping configured in Project Settings -> Input (A/D keys)
	PlayerInputComponent->BindAxis("MoveRight", this, &AMyPaperCharacter::MoveRight);

	// 2. Bind jump actions (configured with the W key in Project Settings -> Input -> Jump)
	PlayerInputComponent->BindAction("Jump", IE_Pressed, this, &AMyPaperCharacter::Jump);
	PlayerInputComponent->BindAction("Jump", IE_Released, this, &AMyPaperCharacter::StopJumping);
}

void AMyPaperCharacter::MoveRight(float Value)
{
	if (Controller != nullptr && Value != 0.0f)
	{
		// 1. Apply movement input along the X axis
		AddMovementInput(FVector(1.0f, 0.0f, 0.0f), Value);

		// 2. Flip the sprite rotation based on the movement direction
		if (Value > 0.0f)
		{
			// Face right
			GetSprite()->SetRelativeRotation(FRotator(0.0f, 0.0f, 0.0f));
		}
		else if (Value < 0.0f)
		{
			// Face left (rotate 180 degrees)
			GetSprite()->SetRelativeRotation(FRotator(0.0f, 180.0f, 0.0f));
		}
	}
}

void AMyPaperCharacter::UnlockDoubleJump()
{
	// Upgrade max jump count to 2 when picking up the item
	JumpMaxCount = 2;
}