// Fill out your copyright notice in the Description page of Project Settings.

#include "MyPaperCharacter.h"
#include "PaperFlipbookComponent.h"
#include "GameFramework/CharacterMovementComponent.h"

AMyPaperCharacter::AMyPaperCharacter()
{
    PrimaryActorTick.bCanEverTick = true;
    JumpMaxCount = 1;

    MaxHealth = 3;
    CurrentHealth = 3;

    bIsDead = false;
    DamageCooldownRemaining = 0.0f;
}

void AMyPaperCharacter::Tick(float DeltaTime)
{
    Super::Tick(DeltaTime);

    if (bIsDead)
    {
        return;
    }

    // Update the damage immunity timer.
    DamageCooldownRemaining = FMath::Max(
        0.0f,
        DamageCooldownRemaining - DeltaTime
    );

    // Falling below the level causes immediate failure.
    if (GetActorLocation().Z < -600.0f)
    {
        bIsDead = true;
        CurrentHealth = 0;

        GetCharacterMovement()->StopMovementImmediately();

        OnHealthChanged(CurrentHealth);
        OnPlayerDied();
        return;
    }

    // Jump animation.
    if (GetCharacterMovement()->IsFalling())
    {
        if (JumpAnimation &&
            GetSprite()->GetFlipbook() != JumpAnimation)
        {
            GetSprite()->SetFlipbook(JumpAnimation);
        }
    }
    else
    {
        // Running and idle animations.
        const float LateralSpeed = GetVelocity().Size2D();

        if (LateralSpeed > 5.0f)
        {
            if (RunAnimation &&
                GetSprite()->GetFlipbook() != RunAnimation)
            {
                GetSprite()->SetFlipbook(RunAnimation);
            }
        }
        else
        {
            if (IdleAnimation &&
                GetSprite()->GetFlipbook() != IdleAnimation)
            {
                GetSprite()->SetFlipbook(IdleAnimation);
            }
        }
    }
}

void AMyPaperCharacter::SetupPlayerInputComponent(
    UInputComponent* PlayerInputComponent)
{
    Super::SetupPlayerInputComponent(PlayerInputComponent);

    PlayerInputComponent->BindAxis(
        "MoveRight",
        this,
        &AMyPaperCharacter::MoveRight
    );

    PlayerInputComponent->BindAction(
        "Jump",
        IE_Pressed,
        this,
        &AMyPaperCharacter::Jump
    );

    PlayerInputComponent->BindAction(
        "Jump",
        IE_Released,
        this,
        &AMyPaperCharacter::StopJumping
    );
}

void AMyPaperCharacter::MoveRight(float Value)
{
    if (bIsDead)
    {
        return;
    }

    if (Controller != nullptr && Value != 0.0f)
    {
        AddMovementInput(
            FVector(1.0f, 0.0f, 0.0f),
            Value
        );

        if (Value > 0.0f)
        {
            GetSprite()->SetRelativeRotation(
                FRotator(0.0f, 0.0f, 0.0f)
            );
        }
        else if (Value < 0.0f)
        {
            GetSprite()->SetRelativeRotation(
                FRotator(0.0f, 180.0f, 0.0f)
            );
        }
    }
}

void AMyPaperCharacter::UnlockDoubleJump()
{
    JumpMaxCount = 2;
}

void AMyPaperCharacter::TakeDamageCustom(int32 DamageAmount)
{
    if (bIsDead ||
        DamageCooldownRemaining > 0.0f ||
        DamageAmount <= 0)
    {
        return;
    }

    // Prevent repeated damage for 1 second.
    DamageCooldownRemaining = 1.0f;

    CurrentHealth = FMath::Clamp(
        CurrentHealth - DamageAmount,
        0,
        MaxHealth
    );

    // Update the HUD through Blueprint.
    OnHealthChanged(CurrentHealth);

    if (CurrentHealth <= 0)
    {
        bIsDead = true;

        GetCharacterMovement()->StopMovementImmediately();

        // Show the failure screen through Blueprint.
        OnPlayerDied();
    }
}