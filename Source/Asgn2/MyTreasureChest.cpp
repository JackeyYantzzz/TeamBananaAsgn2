#include "MyTreasureChest.h"
#include "Components/SphereComponent.h"
#include "PaperFlipbookComponent.h"
#include "PaperFlipbook.h"
#include "MyPaperCharacter.h"
#include "GameFramework/PlayerController.h"
#include "InputCoreTypes.h"
#include "Kismet/GameplayStatics.h"

AMyTreasureChest::AMyTreasureChest()
{
    PrimaryActorTick.bCanEverTick = true;

    FlipbookComponent =
        CreateDefaultSubobject<UPaperFlipbookComponent>(
            TEXT("FlipbookComponent"));
    RootComponent = FlipbookComponent;

    CollisionComponent =
        CreateDefaultSubobject<USphereComponent>(
            TEXT("CollisionComponent"));

    CollisionComponent->InitSphereRadius(80.0f);
    CollisionComponent->SetCollisionProfileName(
        TEXT("OverlapAllDynamic"));
    CollisionComponent->SetGenerateOverlapEvents(true);
    CollisionComponent->SetupAttachment(RootComponent);

    CollisionComponent->OnComponentBeginOverlap.AddDynamic(
        this, &AMyTreasureChest::OnOverlapBegin);

    CollisionComponent->OnComponentEndOverlap.AddDynamic(
        this, &AMyTreasureChest::OnOverlapEnd);

    bIsPlayerNearby = false;
    bIsOpened = false;
}

void AMyTreasureChest::BeginPlay()
{
    Super::BeginPlay();

    // Use the assigned component flipbook if OpenAnimation is empty.
    if (OpenAnimation)
    {
        FlipbookComponent->SetFlipbook(OpenAnimation);
    }

    FlipbookComponent->Stop();
    FlipbookComponent->SetPlaybackPosition(0.0f, false);
    FlipbookComponent->SetLooping(false);
}

void AMyTreasureChest::Tick(float DeltaTime)
{
    Super::Tick(DeltaTime);

    if (bIsOpened || UGameplayStatics::IsGamePaused(this))
    {
        return;
    }

    APlayerController* PC =
        UGameplayStatics::GetPlayerController(this, 0);

    AMyPaperCharacter* Player = PC
        ? Cast<AMyPaperCharacter>(PC->GetPawn())
        : nullptr;

    // Check the actual overlap so multiple player components
    // cannot incorrectly hide the prompt.
    const bool bNearby =
        IsValid(Player) &&
        CollisionComponent->IsOverlappingActor(Player);

    if (bIsPlayerNearby != bNearby)
    {
        bIsPlayerNearby = bNearby;
        OnChestPromptChanged(bIsPlayerNearby);
    }

    if (!bIsPlayerNearby || !PC || Player->CurrentHealth <= 0)
    {
        return;
    }

    if (!PC->WasInputKeyJustPressed(EKeys::E))
    {
        return;
    }

    // Open only once.
    bIsOpened = true;
    OnChestPromptChanged(false);

    FlipbookComponent->SetLooping(false);
    FlipbookComponent->PlayFromStart();

    Player->UnlockDoubleJump();
    OnDoubleJumpUnlocked();
}

void AMyTreasureChest::OnOverlapBegin(
    UPrimitiveComponent* OverlappedComp,
    AActor* OtherActor,
    UPrimitiveComponent* OtherComp,
    int32 OtherBodyIndex,
    bool bFromSweep,
    const FHitResult& SweepResult)
{
    // Tick checks the overlap and updates the UI.
}

void AMyTreasureChest::OnOverlapEnd(
    UPrimitiveComponent* OverlappedComp,
    AActor* OtherActor,
    UPrimitiveComponent* OtherComp,
    int32 OtherBodyIndex)
{
    // Tick checks whether any player component is still overlapping.
}