// Fill out your copyright notice in the Description page of Project Settings.

#include "MyKey.h"
#include "Components/SphereComponent.h"
#include "PaperSpriteComponent.h"
#include "MyPaperCharacter.h"
#include "Kismet/GameplayStatics.h"

AMyKey::AMyKey()
{
	PrimaryActorTick.bCanEverTick = false;

	// Create and set up root collision
	CollisionComponent = CreateDefaultSubobject<USphereComponent>(TEXT("CollisionComponent"));
	CollisionComponent->InitSphereRadius(32.0f);
	CollisionComponent->SetCollisionProfileName(TEXT("OverlapAllDynamic"));
	RootComponent = CollisionComponent;

	// Create and attach sprite component
	SpriteComponent = CreateDefaultSubobject<UPaperSpriteComponent>(TEXT("SpriteComponent"));
	SpriteComponent->SetupAttachment(RootComponent);

	// Bind overlap event
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
			UE_LOG(LogTemp, Warning, TEXT("Level Cleared! Key collected."));

			// Restart or clear the level upon collecting the key
			UGameplayStatics::OpenLevel(GetWorld(), FName(*GetWorld()->GetName()));

			Destroy();
		}
	}
}