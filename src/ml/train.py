import torch
import torch.optim as optim
from model import FireCNN

def main():
    model = FireCNN()
    optimizer = optim.Adam(model.parameters(), lr=1e-3)
    loss_fn = torch.nn.BCELoss()

    for epoch in range(10):
        x = torch.rand(8, 3, 224, 224)
        y = torch.randint(0, 2, (8, 1)).float()

        pred = model(x)
        loss = loss_fn(pred, y)

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        print(f"Epoch {epoch}: loss={loss.item():.4f}")

    torch.save(model.state_dict(), "fire_model.pt")
    print("Saved fire_model.pt")

if __name__ == "__main__":
    main()
