// Fill out your copyright notice in the Description page of Project Settings.

#include "MyGameMode.h"
#include "Kismet/GameplayStatics.h"

AMyGameMode::AMyGameMode()
{
	CollectedDiamondCount = 0;
	TargetDiamondCount = 3; // Default target is 3 diamonds
}

void AMyGameMode::BeginPlay()
{
	Super::BeginPlay();
}

void AMyGameMode::CollectDiamond()
{
	CollectedDiamondCount++;
	UE_LOG(LogTemp, Warning, TEXT("Diamonds Collected: %d / %d"), CollectedDiamondCount, TargetDiamondCount);

	// Check if the target collection count is reached
	if (CollectedDiamondCount >= TargetDiamondCount)
	{
		if (KeyClass)
		{
			UWorld* World = GetWorld();
			if (World)
			{
				FActorSpawnParameters SpawnParams;
				// Spawn the key at the designated location
				World->SpawnActor<AActor>(KeyClass, KeySpawnLocation, FRotator::ZeroRotator, SpawnParams);
				UE_LOG(LogTemp, Warning, TEXT("All diamonds collected! Key has spawned on the map."));
			}
		}
	}
}