// Fill out your copyright notice in the Description page of Project Settings.

#include "MySpikeTrap.h"
#include "Components/BoxComponent.h"
#include "PaperSpriteComponent.h"
#include "PaperSprite.h"
#include "MyPaperCharacter.h" // Replace with your actual character class header
#include "Kismet/GameplayStatics.h"

AMySpikeTrap::AMySpikeTrap()
{
	PrimaryActorTick.bCanEverTick = false;

	// 1. Create the sprite visual component and set it as root
	SpriteComponent = CreateDefaultSubobject<UPaperSpriteComponent>(TEXT("SpriteComponent"));
	RootComponent = SpriteComponent;

	// 2. Create the box collision component for the spikes
	CollisionComponent = CreateDefaultSubobject<UBoxComponent>(TEXT("CollisionComponent"));
	CollisionComponent->InitBoxExtent(FVector(32.0f, 32.0f, 32.0f)); // Adjust size to fit your spike sprite
	CollisionComponent->SetCollisionProfileName(TEXT("OverlapAllDynamic"));
	CollisionComponent->SetupAttachment(RootComponent);

	// 3. Bind the overlap event
	CollisionComponent->OnComponentBeginOverlap.AddDynamic(this, &AMySpikeTrap::OnOverlapBegin);
}

void AMySpikeTrap::BeginPlay()
{
	Super::BeginPlay();
}

void AMySpikeTrap::OnOverlapBegin(UPrimitiveComponent* OverlappedComp, AActor* OtherActor, UPrimitiveComponent* OtherComp, int32 OtherBodyIndex, bool bFromSweep, const FHitResult& SweepResult)
{
	// Check if the overlapping actor is the player character
	if (OtherActor && (OtherActor != this))
	{
		AMyPaperCharacter* Player = Cast<AMyPaperCharacter>(OtherActor);
		if (Player)
		{
			// Deal 1 damage to the player
			Player->TakeDamageCustom(1);
		}
	}
}