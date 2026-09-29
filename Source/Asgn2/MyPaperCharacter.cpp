// Fill out your copyright notice in the Description page of Project Settings.


#include "MyPaperCharacter.h"
#include "PaperFlipbookComponent.h"
#include "Components/InputComponent.h"
#include "GameFramework/CharacterMovementComponent.h"

AMyPaperCharacter::AMyPaperCharacter()
{
	// Set optional default character properties here if needed
}

void AMyPaperCharacter::SetupPlayerInputComponent(UInputComponent* PlayerInputComponent)
{
	Super::SetupPlayerInputComponent(PlayerInputComponent);

	// Bind the "MoveRight" axis mapping configured in Project Settings -> Input
	PlayerInputComponent->BindAxis("MoveRight", this, &AMyPaperCharacter::MoveRight);
}

void AMyPaperCharacter::MoveRight(float Value)
{
	if (Controller != nullptr && Value != 0.0f)
	{
		// 1. Apply movement input along the Y axis (or X axis depending on your 2D setup)
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