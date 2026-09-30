// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "PaperSpriteActor.h"
#include "MyPortal.generated.h"

/**
 * Portal class that handles level completion and key requirements.
 */
UCLASS()
class ASGN2_API AMyPortal : public APaperSpriteActor
{
	GENERATED_BODY()

public:
	AMyPortal();

protected:
	virtual void BeginPlay() override;

	// Sphere collision component for the portal
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Portal")
	class USphereComponent* CollisionComponent;

	// Overlap event handler function
	UFUNCTION()
	void OnOverlapBegin(UPrimitiveComponent* OverlappedComp, AActor* OtherActor, class UPrimitiveComponent* OtherComp, int32 OtherBodyIndex, bool bFromSweep, const FHitResult& SweepResult);

public:
	// Flag indicating whether the player has collected the key
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Portal")
	bool bHasKey;
};