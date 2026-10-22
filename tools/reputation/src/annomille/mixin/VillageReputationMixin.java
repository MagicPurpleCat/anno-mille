package annomille.mixin;

import java.util.concurrent.ThreadLocalRandom;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.ModifyVariable;

/** Репутация в деревнях Millénaire растёт в 5 раз медленнее. Через Village.adjustReputation идут сделки, квесты,
 * бой и команда /reputation: любой положительный прирост делится на 5, остаток добирается случайно (в среднем ровно
 * пятая часть, мелкие начисления не пропадают). Потери репутации не меняются. */
@Pseudo
@Mixin(targets = "org.millenaire.village.Village", remap = false)
public abstract class VillageReputationMixin {
    private static final int SLOWDOWN = 5;

    @ModifyVariable(method = "adjustReputation(Lnet/minecraft/server/level/ServerLevel;Ljava/util/UUID;I)I",
                    at = @At("HEAD"), argsOnly = true, ordinal = 0, remap = false)
    private int annomille$slowGain(int delta) {
        if (delta <= 0) {
            return delta;
        }
        return delta / SLOWDOWN + (ThreadLocalRandom.current().nextInt(SLOWDOWN) < delta % SLOWDOWN ? 1 : 0);
    }
}
