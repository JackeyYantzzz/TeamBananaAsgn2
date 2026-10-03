// Fill out your copyright notice in the Description page of Project Settings.

#include "MyTreasureChest.h"
#include "Components/SphereComponent.h"
#include "PaperFlipbookComponent.h"
#include "PaperFlipbook.h"
#include "MyPaperCharacter.h" // Replace with your actual character class header if needed
#include "GameFramework/CharacterMovementComponent.h"
#include "Kismet/GameplayStatics.h"

AMyTreasureChest::AMyTreasureChest()
{
	PrimaryActorTick.bCanEverTick = true;

	// 1. Create the visual component and set it as the root component
	FlipbookComponent = CreateDefaultSubobject<UPaperFlipbookComponent>(TEXT("FlipbookComponent"));
	RootComponent = FlipbookComponent;

	// 2. Create the sphere collision component (interaction range)
	CollisionComponent = CreateDefaultSubobject<USphereComponent>(TEXT("CollisionComponent"));
	CollisionComponent->InitSphereRadius(80.0f); // Interaction radius
	CollisionComponent->SetCollisionProfileName(TEXT("OverlapAllDynamic"));
	CollisionComponent->SetupAttachment(RootComponent);

	// 3. Bind the overlap events
	CollisionComponent->OnComponentBeginOverlap.AddDynamic(this, &AMyTreasureChest::OnOverlapBegin);
	CollisionComponent->OnComponentEndOverlap.AddDynamic(this, &AMyTreasureChest::OnOverlapEnd);

	bIsPlayerNearby = false;
	bIsOpened = false;
}

void AMyTreasureChest::BeginPlay()
{
	Super::BeginPlay();

	// At game start: set the flipbook, stop playing, and lock to the first frame (closed state)
	if (OpenAnimation && FlipbookComponent)
	{
		FlipbookComponent->SetFlipbook(OpenAnimation);
		FlipbookComponent->Stop();
		FlipbookComponent->SetPlaybackPosition(0.0f, false);
		FlipbookComponent->SetLooping(false);
	}
}

void AMyTreasureChest::Tick(float DeltaTime)
{
	Super::Tick(DeltaTime);

	// Only check when player is nearby and chest is NOT opened yet
	if (bIsPlayerNearby && !bIsOpened)
	{
		APlayerController* PC = UGameplayStatics::GetPlayerController(this, 0);
		// Use WasInputKeyJustPressed to trigger ONLY ONCE per press
		if (PC && PC->WasInputKeyJustPressed(EKeys::E))
		{
			bIsOpened = true; // Lock immediately so this code runs only once

			// Play the chest opening animation from start once without looping
			if (OpenAnimation)
			{
				FlipbookComponent->PlayFromStart();
				FlipbookComponent->SetLooping(false);
			}

			// Get the player character and grant the double jump ability
			AMyPaperCharacter* Player = Cast<AMyPaperCharacter>(UGameplayStatics::GetPlayerCharacter(this, 0));
			if (Player)
			{
				Player->JumpMaxCount = 2;
				GEngine->AddOnScreenDebugMessage(-1, 5.0f, FColor::Green, TEXT("Double Jump Unlocked!"));
			}
		}
	}
}

void AMyTreasureChest::OnOverlapBegin(UPrimitiveComponent* OverlappedComp, AActor* OtherActor, UPrimitiveComponent* OtherComp, int32 OtherBodyIndex, bool bFromSweep, const FHitResult& SweepResult)
{
	if (OtherActor && (OtherActor != this))
	{
		AMyPaperCharacter* Player = Cast<AMyPaperCharacter>(OtherActor);
		if (Player)
		{
			bIsPlayerNearby = true;
			GEngine->AddOnScreenDebugMessage(-1, 3.0f, FColor::Yellow, TEXT("Press E to open chest"));
		}
	}
}

void AMyTreasureChest::OnOverlapEnd(UPrimitiveComponent* OverlappedComp, AActor* OtherActor, UPrimitiveComponent* OtherComp, int32 OtherBodyIndex)
{
	if (OtherActor && (OtherActor != this))
	{
		AMyPaperCharacter* Player = Cast<AMyPaperCharacter>(OtherActor);
		if (Player)
		{
			bIsPlayerNearby = false;
		}
	}
}