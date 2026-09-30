// Fill out your copyright notice in the Description page of Project Settings.

#include "MyDiamond.h"
#include "Components/SphereComponent.h"
#include "PaperSpriteComponent.h"
#include "MyPaperCharacter.h"
#include "MyGameMode.h"
#include "Kismet/GameplayStatics.h"

AMyDiamond::AMyDiamond()
{
	PrimaryActorTick.bCanEverTick = false;

	// Create and set up the root collision component
	CollisionComponent = CreateDefaultSubobject<USphereComponent>(TEXT("CollisionComponent"));
	CollisionComponent->InitSphereRadius(32.0f);
	CollisionComponent->SetCollisionProfileName(TEXT("OverlapAllDynamic"));
	RootComponent = CollisionComponent;

	// Create and attach the sprite component
	SpriteComponent = CreateDefaultSubobject<UPaperSpriteComponent>(TEXT("SpriteComponent"));
	SpriteComponent->SetupAttachment(RootComponent);

	// Bind the overlap event
	CollisionComponent->OnComponentBeginOverlap.AddDynamic(this, &AMyDiamond::OnOverlapBegin);
}

void AMyDiamond::BeginPlay()
{
	Super::BeginPlay();
}

void AMyDiamond::OnOverlapBegin(UPrimitiveComponent* OverlappedComp, AActor* OtherActor, class UPrimitiveComponent* OtherComp, int32 OtherBodyIndex, bool bFromSweep, const FHitResult& SweepResult)
{
	if (OtherActor && (OtherActor != this))
	{
		AMyPaperCharacter* PlayerCharacter = Cast<AMyPaperCharacter>(OtherActor);
		if (PlayerCharacter)
		{
			// Notify the GameMode that a diamond has been collected
			AMyGameMode* MyGameMode = Cast<AMyGameMode>(UGameplayStatics::GetGameMode(GetWorld()));
			if (MyGameMode)
			{
				MyGameMode->CollectDiamond();
			}

			// Destroy the diamond actor
			Destroy();
		}
	}
}
