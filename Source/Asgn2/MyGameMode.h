// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/GameModeBase.h"
#include "MyGameMode.generated.h"

/**
 * Custom GameMode to track diamond collection and spawn the key when the target is reached.
 */
UCLASS()
class ASGN2_API AMyGameMode : public AGameModeBase
{
	GENERATED_BODY()

public:
	AMyGameMode();

	// Called when the player collects a diamond
	void CollectDiamond();

	// Target number of diamonds required to spawn the key
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "GameRules")
	int32 TargetDiamondCount = 3;

	// Current number of collected diamonds
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "GameRules")
	int32 CollectedDiamondCount = 0;

	// The Key actor class to spawn (assign your BP_Key blueprint here)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "GameRules")
	TSubclassOf<class AActor> KeyClass;

	// World coordinates where the key will spawn
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "GameRules")
	FVector KeySpawnLocation;

protected:
	virtual void BeginPlay() override;
};