// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "PaperCharacter.h"
#include "MyPaperCharacter.generated.h"

UCLASS()
class ASGN2_API AMyPaperCharacter : public APaperCharacter
{
	GENERATED_BODY()

public:
	AMyPaperCharacter();

	virtual void Tick(float DeltaTime) override;

	UFUNCTION(BlueprintCallable, Category = "Abilities")
	void UnlockDoubleJump();

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Animations")
	class UPaperFlipbook* JumpAnimation;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Animations")
	class UPaperFlipbook* RunAnimation;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Animations")
	class UPaperFlipbook* IdleAnimation;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Health")
	int32 MaxHealth = 3;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Health")
	int32 CurrentHealth = 3;

	UFUNCTION(BlueprintCallable, Category = "Health")
	virtual void TakeDamageCustom(int32 DamageAmount);

	// Update the health images in Blueprint.
	UFUNCTION(BlueprintImplementableEvent, Category = "Health")
	void OnHealthChanged(int32 NewHealth);

	// Show the failure UI in Blueprint.
	UFUNCTION(BlueprintImplementableEvent, Category = "Health")
	void OnPlayerDied();

protected:
	bool bIsDead = false;

	float DamageCooldownRemaining = 0.0f;

	void MoveRight(float Value);

	virtual void SetupPlayerInputComponent(
		class UInputComponent* PlayerInputComponent
	) override;
};