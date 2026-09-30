// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "MyKey.generated.h"

UCLASS()
class ASGN2_API AMyKey : public AActor
{
	GENERATED_BODY()

public:
	AMyKey();

protected:
	virtual void BeginPlay() override;

	// Collision component for the key
	UPROPERTY(VisibleAnywhere, Category = "Components")
	class USphereComponent* CollisionComponent;

	// Sprite component for the key visual
	UPROPERTY(VisibleAnywhere, Category = "Components")
	class UPaperSpriteComponent* SpriteComponent;

	// Overlap event function for level completion
	UFUNCTION()
	void OnOverlapBegin(class UPrimitiveComponent* OverlappedComp, class AActor* OtherActor, class UPrimitiveComponent* OtherComp, int32 OtherBodyIndex, bool bFromSweep, const FHitResult& SweepResult);
};