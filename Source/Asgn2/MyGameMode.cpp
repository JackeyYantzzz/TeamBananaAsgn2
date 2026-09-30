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
				// Dynamically get the player character's current location in the world
				APawn* PlayerPawn = UGameplayStatics::GetPlayerPawn(World, 0);
				if (PlayerPawn)
				{
					FVector PlayerLocation = PlayerPawn->GetActorLocation();

					// Set the spawn location to be slightly in front of the player (e.g., 150 units ahead on the X axis)
					FVector SpawnLocation = PlayerLocation + FVector(150.0f, 0.0f, 50.0f);

					FActorSpawnParameters SpawnParams;
					World->SpawnActor<AActor>(KeyClass, SpawnLocation, FRotator::ZeroRotator, SpawnParams);
					UE_LOG(LogTemp, Warning, TEXT("All diamonds collected! Key spawned in front of the player."));
				}
			}
		}
	}
}