// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "MySpikeTrap.generated.h"

UCLASS()
class ASGN2_API AMySpikeTrap : public AActor
{
	GENERATED_BODY()

public:
	AMySpikeTrap();

protected:
	virtual void BeginPlay() override;

	// Visual component for the spike trap (static sprite)
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	class UPaperSpriteComponent* SpriteComponent;

	// Box collision component to detect player touch
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	class UBoxComponent* CollisionComponent;

	// Overlap begin event (player touches the spikes)
	UFUNCTION()
	void OnOverlapBegin(UPrimitiveComponent* OverlappedComp, AActor* OtherActor, UPrimitiveComponent* OtherComp, int32 OtherBodyIndex, bool bFromSweep, const FHitResult& SweepResult);
};