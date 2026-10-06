// Fill out your copyright notice in the Description page of Project Settings.

#include "MyKey.h"
#include "Components/SphereComponent.h"
#include "PaperSpriteComponent.h"
#include "MyPaperCharacter.h"
#include "MyPortal.h"
#include "Kismet/GameplayStatics.h"
#include "Engine/World.h"

AMyKey::AMyKey()
{
	PrimaryActorTick.bCanEverTick = false;

	// 1. Create the collision component first and set it as the RootComponent
	CollisionComponent = CreateDefaultSubobject<USphereComponent>(TEXT("CollisionComponent"));
	CollisionComponent->InitSphereRadius(40.0f);
	CollisionComponent->SetCollisionProfileName(TEXT("OverlapAllDynamic"));
	RootComponent = CollisionComponent; // Set as root

	// 2. Create the Sprite component and attach it to the collision component
	SpriteComponent = CreateDefaultSubobject<UPaperSpriteComponent>(TEXT("SpriteComponent"));
	SpriteComponent->SetupAttachment(RootComponent);
	SpriteComponent->SetRelativeLocation(FVector::ZeroVector);

	// 3. Bind the overlap event
	CollisionComponent->OnComponentBeginOverlap.AddDynamic(this, &AMyKey::OnOverlapBegin);
}

void AMyKey::BeginPlay()
{
	Super::BeginPlay();
}

void AMyKey::OnOverlapBegin(UPrimitiveComponent* OverlappedComp, AActor* OtherActor, class UPrimitiveComponent* OtherComp, int32 OtherBodyIndex, bool bFromSweep, const FHitResult& SweepResult)
{
	if (OtherActor && (OtherActor != this))
	{
		AMyPaperCharacter* PlayerCharacter = Cast<AMyPaperCharacter>(OtherActor);
		if (PlayerCharacter)
		{
			GEngine->AddOnScreenDebugMessage(-1, 5.0f, FColor::Yellow, TEXT("Key Collected!"));

			// Find all portals in the world and set their bHasKey status to true
			TArray<AActor*> FoundPortals;
			UGameplayStatics::GetAllActorsOfClass(GetWorld(), AMyPortal::StaticClass(), FoundPortals);
			for (AActor* PortalActor : FoundPortals)
			{
				AMyPortal* Portal = Cast<AMyPortal>(PortalActor);
				if (Portal)
				{
					Portal->bHasKey = true;
					Portal->SetActorHiddenInGame(false);
					Portal->SetActorEnableCollision(true);
				}
			}

			// Destroy the key actor after collection
			Destroy();
		}
	}
}