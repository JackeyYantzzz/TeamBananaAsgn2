// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "PaperCharacter.h"
#include "MyPaperCharacter.generated.h"

/**
 *
 */
UCLASS()
class ASGN2_API AMyPaperCharacter : public APaperCharacter
{
	GENERATED_BODY()

public:
	AMyPaperCharacter();

protected:
	// Handles left/right movement input
	void MoveRight(float Value);

	// Override to bind player input
	virtual void SetupPlayerInputComponent(class UInputComponent* PlayerInputComponent) override;
};