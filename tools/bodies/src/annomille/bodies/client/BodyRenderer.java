package annomille.bodies.client;

import com.mojang.blaze3d.vertex.PoseStack;

import annomille.bodies.Bodies;
import annomille.bodies.BodyEntity;
import net.minecraft.client.Minecraft;
import net.minecraft.client.model.PlayerModel;
import net.minecraft.client.model.geom.ModelLayers;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.LivingEntityRenderer;
import net.minecraft.client.resources.PlayerSkin;
import net.minecraft.resources.ResourceLocation;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.client.event.EntityRenderersEvent;

/** Тело рисуется моделью игрока с его скином, сидя на земле. */
@EventBusSubscriber(modid = Bodies.MODID, bus = EventBusSubscriber.Bus.MOD, value = Dist.CLIENT)
public class BodyRenderer extends LivingEntityRenderer<BodyEntity, PlayerModel<BodyEntity>> {
    private final PlayerModel<BodyEntity> wide, slim;

    public BodyRenderer(EntityRendererProvider.Context ctx) {
        super(ctx, new PlayerModel<>(ctx.bakeLayer(ModelLayers.PLAYER), false), 0.5F);
        wide = model;
        slim = new PlayerModel<>(ctx.bakeLayer(ModelLayers.PLAYER_SLIM), true);
    }

    @SubscribeEvent
    public static void register(EntityRenderersEvent.RegisterRenderers e) {
        e.registerEntityRenderer(Bodies.BODY.get(), BodyRenderer::new);
    }

    private static PlayerSkin skin(BodyEntity b) {
        return Minecraft.getInstance().getSkinManager().getInsecureSkin(b.profile());
    }

    @Override
    public void render(BodyEntity b, float yaw, float pt, PoseStack ps, MultiBufferSource buf, int light) {
        model = skin(b).model() == PlayerSkin.Model.SLIM ? slim : wide;
        super.render(b, yaw, pt, ps, buf, light);
    }

    @Override
    public ResourceLocation getTextureLocation(BodyEntity b) {
        return skin(b).texture();
    }

    @Override
    protected void scale(BodyEntity b, PoseStack ps, float pt) {
        model.riding = true;  // поза «сидит»; флаг выставлен в render() раньше, здесь перекрываем
        ps.scale(0.9375F, 0.9375F, 0.9375F);
        ps.translate(0.0F, 0.65F, 0.0F);  // ось y здесь перевёрнута: опускаем на землю
    }
}
