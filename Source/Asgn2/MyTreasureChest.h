// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "MyTreasureChest.generated.h"

UCLASS()
class ASGN2_API AMyTreasureChest : public AActor
{
	GENERATED_BODY()

public:
	AMyTreasureChest();

protected:
	virtual void BeginPlay() override;

	// Visual component for the chest (Paper Flipbook)
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	class UPaperFlipbookComponent* FlipbookComponent;

	// Sphere collision component to detect nearby players
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	class USphereComponent* CollisionComponent;

	// Reference to the chest opening animation asset
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Animation")
	class UPaperFlipbook* OpenAnimation;

	// Tracks whether the player is within interaction range
	bool bIsPlayerNearby;

	// Tracks whether the chest has already been opened
	bool bIsOpened;

	// Overlap begin event (player enters range)
	UFUNCTION()
	void OnOverlapBegin(UPrimitiveComponent* OverlappedComp, AActor* OtherActor, UPrimitiveComponent* OtherComp, int32 OtherBodyIndex, bool bFromSweep, const FHitResult& SweepResult);

	// Overlap end event (player leaves range)
	UFUNCTION()
	void OnOverlapEnd(UPrimitiveComponent* OverlappedComp, AActor* OtherActor, UPrimitiveComponent* OtherComp, int32 OtherBodyIndex);

public:
	// Called every frame to listen for the E key input
	virtual void Tick(float DeltaTime) override;
};