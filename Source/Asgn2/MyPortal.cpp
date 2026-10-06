// Fill out your copyright notice in the Description page of Project Settings.

#include "MyPortal.h"
#include "Components/SphereComponent.h"
#include "PaperFlipbookComponent.h"
#include "PaperSpriteComponent.h"
#include "MyPaperCharacter.h"
#include "Kismet/GameplayStatics.h"

AMyPortal::AMyPortal()
{
	PrimaryActorTick.bCanEverTick = false;

	// Create the collision component and attach it to the existing RootComponent (RenderComponent)
	CollisionComponent = CreateDefaultSubobject<USphereComponent>(TEXT("CollisionComponent"));
	CollisionComponent->InitSphereRadius(40.0f);
	CollisionComponent->SetCollisionProfileName(TEXT("OverlapAllDynamic"));

	// Attach collision to the root sprite component so both sprite and collision work together
	CollisionComponent->SetupAttachment(RootComponent);

	// Bind the overlap event
	CollisionComponent->OnComponentBeginOverlap.AddDynamic(this, &AMyPortal::OnOverlapBegin);

	// Initialize key status to false
	bHasKey = false;
}

void AMyPortal::BeginPlay()
{
	Super::BeginPlay();

	// Locked portals start hidden and cannot be entered.
	SetActorHiddenInGame(!bHasKey);
	SetActorEnableCollision(bHasKey);
}

void AMyPortal::OnOverlapBegin(UPrimitiveComponent* OverlappedComp, AActor* OtherActor, class UPrimitiveComponent* OtherComp, int32 OtherBodyIndex, bool bFromSweep, const FHitResult& SweepResult)
{
	if (OtherActor && (OtherActor != this))
	{
		AMyPaperCharacter* PlayerCharacter = Cast<AMyPaperCharacter>(OtherActor);
		if (PlayerCharacter)
		{
			// Check if the player has the key to unlock the portal
			if (bHasKey && !bVictoryTriggered)
			{
				bVictoryTriggered = true;
				OnPortalVictory();
			}
		}
	}
}