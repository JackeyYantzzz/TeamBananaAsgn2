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

	// Tick function to detect movement/jump state and switch animations
	virtual void Tick(float DeltaTime) override;

	// Function called when picking up an item to unlock double jump
	UFUNCTION(BlueprintCallable, Category = "Abilities")
	void UnlockDoubleJump();

	// Jump animation
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Animations")
	class UPaperFlipbook* JumpAnimation;

	// Running/Walking animation
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Animations")
	class UPaperFlipbook* RunAnimation;

	// Idle animation (leave empty or assign a static sprite if desired when standing still)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Animations")
	class UPaperFlipbook* IdleAnimation;

	// --- Health System Properties ---
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Health")
	int32 MaxHealth = 3;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Health")
	int32 CurrentHealth = 3;

	// Function to handle taking damage (called by spike trap or enemies)
	UFUNCTION(BlueprintCallable, Category = "Health")
	virtual void TakeDamageCustom(int32 DamageAmount);

protected:
	// Handles left/right movement input
	void MoveRight(float Value);

	// Override to bind player input
	virtual void SetupPlayerInputComponent(class UInputComponent* PlayerInputComponent) override;
};